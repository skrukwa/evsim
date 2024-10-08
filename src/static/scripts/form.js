const lessStopsButton = document.getElementById('less-stops-button')
const balancedStopsButton = document.getElementById('balanced-stops-button')
const moreStopsButton = document.getElementById('more-stops-button')

const minLegLengthSlider = document.getElementById('min-leg-length-slider')
const minLegLengthInput = document.getElementById('min-leg-length-input')

const evRangeSlider = document.getElementById('ev-range-slider')
const evRangeInput = document.getElementById('ev-range-input')

const minBatterySlider = document.getElementById('min-battery-slider')
const minBatteryInput = document.getElementById('min-battery-input')

const maxBatterySlider = document.getElementById('max-battery-slider')
const maxBatteryInput = document.getElementById('max-battery-input')

const startBatterySlider = document.getElementById('start-battery-slider')
const startBatteryInput = document.getElementById('start-battery-input')

const advancedOptions = document.getElementById('advanced-options')
const advancedOptionsError = document.getElementById('advanced-options-error')
const advancedOptionsButton = document.getElementById('advanced-options-button')

const submitButton = document.getElementById('submit-button')

const lessStops = {
    'min-leg-length': 400, 'ev-range': 550, 'min-battery': 15, 'max-battery': 100, 'start-battery': 40
}
const balancedStops = {
    'min-leg-length': 250, 'ev-range': 550, 'min-battery': 15, 'max-battery': 100, 'start-battery': 40
}
const moreStops = {
    'min-leg-length': 100, 'ev-range': 550, 'min-battery': 15, 'max-battery': 100, 'start-battery': 40
}

initInputPair(minLegLengthSlider, minLegLengthInput)
requirementsListen(minLegLengthSlider)
requirementsListen(minLegLengthInput)

initInputPair(evRangeSlider, evRangeInput)
requirementsListen(evRangeSlider)
requirementsListen(evRangeInput)

initInputPair(minBatterySlider, minBatteryInput)
requirementsListen(minBatterySlider)
requirementsListen(minBatteryInput)

initInputPair(maxBatterySlider, maxBatteryInput)
requirementsListen(maxBatterySlider)
requirementsListen(maxBatteryInput)

initInputPair(startBatterySlider, startBatteryInput)
requirementsListen(startBatterySlider)
requirementsListen(startBatteryInput)

updateActiveStops()
updateRequirements()

lessStopsButton.addEventListener('click', () => {
    minLegLengthSlider.value = lessStops['min-leg-length']
    minLegLengthInput.value = lessStops['min-leg-length']
    evRangeSlider.value = lessStops['ev-range']
    evRangeInput.value = lessStops['ev-range']
    minBatterySlider.value = lessStops['min-battery']
    minBatteryInput.value = lessStops['min-battery']
    maxBatterySlider.value = lessStops['max-battery']
    maxBatteryInput.value = lessStops['max-battery']
    startBatterySlider.value = lessStops['start-battery']
    startBatteryInput.value = lessStops['start-battery']
    updateRequirements()
})

balancedStopsButton.addEventListener('click', () => {
    minLegLengthSlider.value = balancedStops['min-leg-length']
    minLegLengthInput.value = balancedStops['min-leg-length']
    evRangeSlider.value = balancedStops['ev-range']
    evRangeInput.value = balancedStops['ev-range']
    minBatterySlider.value = balancedStops['min-battery']
    minBatteryInput.value = balancedStops['min-battery']
    maxBatterySlider.value = balancedStops['max-battery']
    maxBatteryInput.value = balancedStops['max-battery']
    startBatterySlider.value = balancedStops['start-battery']
    startBatteryInput.value = balancedStops['start-battery']
    updateRequirements()
})

moreStopsButton.addEventListener('click', () => {
    minLegLengthSlider.value = moreStops['min-leg-length']
    minLegLengthInput.value = moreStops['min-leg-length']
    evRangeSlider.value = moreStops['ev-range']
    evRangeInput.value = moreStops['ev-range']
    minBatterySlider.value = moreStops['min-battery']
    minBatteryInput.value = moreStops['min-battery']
    maxBatterySlider.value = moreStops['max-battery']
    maxBatteryInput.value = moreStops['max-battery']
    startBatterySlider.value = moreStops['start-battery']
    startBatteryInput.value = moreStops['start-battery']
    updateRequirements()
})

advancedOptionsButton.addEventListener('click', () => {
    if (advancedOptions.style.display === 'none') {
        advancedOptions.style.display = 'grid'
        advancedOptionsButton.innerText = 'hide advanced options'
    } else {
        advancedOptions.style.display = 'none'
        advancedOptionsButton.innerText = 'advanced options'
    }
})

function initInputPair(slider, input) {
    input.value = slider.value

    slider.addEventListener('input', () => {
        input.value = slider.value
    })
    input.addEventListener('input', () => {
        slider.value = input.value
    })
}

function updateActiveStops() {
    const effectiveRange = parseFloat(evRangeInput.value) * (parseFloat(maxBatterySlider.value) - parseFloat(minBatterySlider.value)) / 100
    const minLegLength = parseFloat(minLegLengthInput.value)
    if (minLegLength < (1 / 3) * effectiveRange) {
        lessStopsButton.checked = true
    } else if (minLegLength < (2 / 3) * effectiveRange) {
        balancedStopsButton.checked = true
    } else if (minLegLength < effectiveRange) {
        moreStopsButton.checked = true
    } else {
        lessStopsButton.checked = false
        balancedStopsButton.checked = false
        moreStopsButton.checked = false
    }
}

function updateRequirements() {
    if (parseFloat(minBatteryInput.value) >= parseFloat(maxBatteryInput.value)) {
        advancedOptionsError.innerText = `min battery (${minBatteryInput.value}) must be less than to max battery (${maxBatteryInput.value})`
        submitButton.disabled = true
        lessStopsButton.checked = false
        balancedStopsButton.checked = false
        moreStopsButton.checked = false
        return
    }

    const effectiveRange = parseFloat(evRangeInput.value) * (parseFloat(maxBatterySlider.value) - parseFloat(minBatterySlider.value)) / 100
    if (effectiveRange > 700) {
        advancedOptionsError.innerText = `effective range (${effectiveRange}) must be less than 700`
        submitButton.disabled = true
        lessStopsButton.checked = false
        balancedStopsButton.checked = false
        moreStopsButton.checked = false
        return
    }

    const minLegLength = parseFloat(minLegLengthInput.value)
    if (minLegLength >= effectiveRange) {
        advancedOptionsError.innerText = `min leg length (${minLegLength}) must be less than effective range (${effectiveRange})`
        submitButton.disabled = true
        lessStopsButton.checked = false
        balancedStopsButton.checked = false
        moreStopsButton.checked = false
        return
    }

    submitButton.disabled = false
    advancedOptionsError.innerText = ''
}

function requirementsListen(element) {
    element.addEventListener('input', () => {
        updateActiveStops()
        updateRequirements()
    })
}
