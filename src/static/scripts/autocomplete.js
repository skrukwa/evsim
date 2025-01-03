const startLocationContainer = document.getElementById('start-location-container')
const startLocationInput = document.getElementById('start-location-input')
const startLatInput = document.getElementById('start-lat-input')
const startLngInput = document.getElementById('start-lng-input')
const currentStartUUID = {'uuid': null, createdAt: null}

const endLocationContainer = document.getElementById('end-location-container')
const endLocationInput = document.getElementById('end-location-input')
const endLatInput = document.getElementById('end-lat-input')
const endLngInput = document.getElementById('end-lng-input')
const currentEndUUID = {'uuid': null, createdAt: null}

const errorNotification = document.getElementById('error-notification')

addAutocompleteListener(startLocationInput, startLocationContainer, startLatInput, startLngInput, currentStartUUID)
addAutocompleteListener(endLocationInput, endLocationContainer, endLatInput, endLngInput, currentEndUUID)

document.addEventListener('click', (event) => {

    // check if user is done typing in start input
    if (!startLocationInput.contains(event.target)) {
        // clear start input if user has not selected a prediction
        if (startLatInput.value === '' || startLngInput.value === '') {
            startLocationInput.value = ''
        }
        // remove start predictions
        startLocationContainer.querySelector('.autocomplete-items')?.remove()

    }

    // check if user is done typing in end input
    if (!endLocationInput.contains(event.target)) {
        // clear end input if user has not selected a prediction
        if (endLatInput.value === '' || endLngInput.value === '') {
            endLocationInput.value = ''
        }
        // remove end predictions
        endLocationContainer.querySelector('.autocomplete-items')?.remove()
    }
})

function addAutocompleteListener(inputElement, inputElementContainer, latElement, lngElement, uuid) {

    inputElement.addEventListener('input', async () => {
        // invalidate previous pat/lng on new input
        latElement.value = ''
        lngElement.value = ''

        // early return
        if (inputElement.value.length < 3) {
            return
        }

        // generate a new UUID if needed
        if (uuid.uuid === null || Date.now() - currentStartUUID.createdAt > 2 * 60 * 1000) {
            uuid.uuid = self.crypto.randomUUID()
            uuid.createdAt = Date.now()
        }

        // fetch predictions
        const resp = await fetch(`/googleapis/maps/api/place/autocomplete/json?`
            + `input=${inputElement.value}`
            + `&components=country:us|country:ca`
            + `&language=en`
            + `&sessiontoken=${uuid.uuid}`)
        const data = await resp.json()

        // check for error
        if (data['status'] !== 'OK') {
            errorNotification.textContent = data['error_message']
            errorNotification.classList.add('show')
            setTimeout(() => {
                errorNotification.classList.remove('show')
            }, 5000)
            return
        }

        displayPredictions(inputElement, inputElementContainer, data['predictions'], latElement, lngElement, uuid)
    })
}

function displayPredictions(inputElement, inputElementContainer, predictions, latElement, lngElement, uuid) {
    // remove old autocomplete items
    inputElementContainer.querySelector('.autocomplete-items')?.remove()

    // early return if no predictions
    if (predictions.length === 0) {
        return
    }

    // create autocomplete items container
    const items = document.createElement('div')
    items.setAttribute('class', 'autocomplete-items')
    inputElement.parentNode.appendChild(items)

    // create dropdown items for predictions
    for (let prediction of predictions) {
        const description = prediction['description']
        const placeID = prediction['place_id']
        const mainText = prediction['structured_formatting']['main_text']
        const matches = prediction['structured_formatting']['main_text_matched_substrings']
        const secondaryText = prediction['structured_formatting']['secondary_text']

        const item = document.createElement('div')
        let currentIndex = 0
        for (let match of matches) {
            const matchOffset = match['offset']
            const matchLength = match['length']
            item.innerHTML += mainText.slice(currentIndex, matchOffset) +
                '<strong>' +
                mainText.slice(matchOffset, matchOffset + matchLength) +
                '</strong>'
            currentIndex = matchOffset + matchLength
        }
        item.innerHTML += mainText.slice(currentIndex) + ' <span>' + secondaryText + '</span>'

        // handle click on a prediction
        item.addEventListener('click', async () => {
            // generate a new UUID if needed
            if (uuid.uuid === null || Date.now() - currentStartUUID.createdAt > 2 * 60 * 1000) {
                uuid.uuid = self.crypto.randomUUID()
                uuid.createdAt = Date.now()
            }

            // set temp lat/lng values so that the input is not cleared by the document click handler
            // which will be the next event in the event loop while awaiting the fetch below
            latElement.value = '9.99'
            lngElement.value = '9.99'

            // fetch place details
            const resp = await fetch(`/googleapis/maps/api/place/details/json?`
                + `place_id=${placeID}`
                + `&fields=geometry`
                + `&language=en`
                + `&sessiontoken=${uuid.uuid}`)
            const data = await resp.json()

            // invalidate UUID
            uuid.uuid = null
            uuid.createdAt = null

            // check for error
            if (data['status'] !== 'OK') {
                errorNotification.textContent = data['error_message']
                errorNotification.classList.add('show')
                setTimeout(() => {
                    errorNotification.classList.remove('show')
                }, 5000)
                inputElement.value = ''
                latElement.value = ''
                lngElement.value = ''
                return
            }

            // update input values
            inputElement.value = description
            latElement.value = data['result']['geometry']['location']['lat']
            lngElement.value = data['result']['geometry']['location']['lng']
        })

        items.appendChild(item)
    }
}
