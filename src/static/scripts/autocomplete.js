const startLocationInput = document.getElementById('start-location-input')
const startLatInput = document.getElementById('start-lat-input')
const startLngInput = document.getElementById('start-lng-input')
const currentStartUUID = {'uuid': null, createdAt: null}

const endLocationInput = document.getElementById('end-location-input')
const endLatInput = document.getElementById('end-lat-input')
const endLngInput = document.getElementById('end-lng-input')
const currentEndUUID = {'uuid': null, createdAt: null}

const errorNotification = document.getElementById('error-notification')

addAutocompleteListener(startLocationInput, startLatInput, startLngInput, currentStartUUID)
addAutocompleteListener(endLocationInput, endLatInput, endLngInput, currentEndUUID)

document.addEventListener('click', (event) => {
    // when the user clicks anywhere in the document, close the dropdowns
    const items = document.querySelector('.autocomplete-items')
    if (items) {
        items.remove()
    }
})

function addAutocompleteListener(inputElement, latElement, lngElement, uuid) {
    inputElement.addEventListener('input', async () => {
        // early return
        if (inputElement.value.length < 3) {
            return
        }

        // generate a new UUID if needed
        if (uuid.uuid === null || Date.now() - currentStartUUID.createdAt > 2 * 60 * 1000) {
            uuid.uuid = self.crypto.randomUUID()
            uuid.createdAt = Date.now()
        }

        // fetch suggestions
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
        }

        // display suggestions
        autocomplete(inputElement, data['predictions'], latElement, lngElement, uuid)
    })
}


function autocomplete(inputElement, predictions, latElement, lngElement, uuid) {
    // check and remove old .autocomplete-items div
    const oldItems = inputElement.parentNode.querySelector('.autocomplete-items')
    if (oldItems) {
        oldItems.remove()
    }

    // early return
    if (predictions.length === 0) {
        return
    }

    // create autocomplete-items div
    const items = document.createElement('div')
    items.setAttribute('class', 'autocomplete-items')
    inputElement.parentNode.appendChild(items)

    // create new elements
    for (let prediction of predictions) {
        const description = prediction['description']
        const placeID = prediction['place_id']
        const mainText = prediction['structured_formatting']['main_text']
        const matches = prediction['structured_formatting']['main_text_matched_substrings']
        const secondaryText = prediction['structured_formatting']['secondary_text']

        // create dropdown autocomplete item
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
        item.addEventListener('click', async () => {

            // update input value
            inputElement.value = description

            // generate a new UUID if needed
            if (uuid.uuid === null || Date.now() - currentStartUUID.createdAt > 2 * 60 * 1000) {
                uuid.uuid = self.crypto.randomUUID()
                uuid.createdAt = Date.now()
            }

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
            }

            // update hidden input values
            latElement.value = data['result']['geometry']['location']['lat']
            lngElement.value = data['result']['geometry']['location']['lng']
        })
        items.appendChild(item)
    }
}
