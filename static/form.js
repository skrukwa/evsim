const auto1 = document.getElementById('auto-fill-1')
const auto2 = document.getElementById('auto-fill-2')

const startLat = document.getElementById('start-lat')

const startLon = document.getElementById('start-lon')

const endLat = document.getElementById('end-lat')

const endLon = document.getElementById('end-lon')

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

const req1 = document.getElementById('input-req-1')
const req2 = document.getElementById('input-req-2')
const req3 = document.getElementById('input-req-3')
const req4L = document.getElementById('input-req-4-l')
const req4M = document.getElementById('input-req-4-m')
const req4R = document.getElementById('input-req-4-r')

const submitButton = document.getElementById('submit-button')

function doAuto1() {
    const latLAX = 33.9434
    const lonLAX = -118.4095
    const latJFK = 40.6438
    const lonJFK = -73.7822
    startLat.value = latLAX
    startLon.value = lonLAX
    endLat.value = latJFK
    endLon.value = lonJFK
}

function doAuto2() {
    const latYVR = 49.1953
    const lonYVR = -123.1785
    const latMIA = 25.7951
    const lonMIA = -80.2797
    startLat.value = latYVR
    startLon.value = lonYVR
    endLat.value = latMIA
    endLon.value = lonMIA
}

function link(slider, input) {
    input.value = slider.value

    slider.addEventListener('input', () => {
        input.value = slider.value 
    })
    input.addEventListener('input', () => {
        slider.value = input.value
    })
}

function requirementsListen(element) {
    element.addEventListener('input', () => {
        updateRequirements()
    })
}

function updateRequirements() {

    const green = '#008000'
    const red = '#ff0000'
    
    const lats = /^-?[0-9]+(\.[0-9]+)?$/.test(startLat.value) ? parseFloat(startLat.value) : -999
    const lons = /^-?[0-9]+(\.[0-9]+)?$/.test(startLon.value) ? parseFloat(startLon.value) : -999
    const late = /^-?[0-9]+(\.[0-9]+)?$/.test(endLat.value) ? parseFloat(endLat.value) : -999
    const lone = /^-?[0-9]+(\.[0-9]+)?$/.test(endLon.value) ? parseFloat(endLon.value) : -999
    const llmin = parseFloat(minLegLengthInput.value)
    const r = parseFloat(evRangeInput.value)
    const bmin = parseFloat(minBatteryInput.value) / 100
    const bmax = parseFloat(maxBatteryInput.value) / 100

    let en = true

    if (20 <= lats && lats <= 70 && 20 <= late && late <= 70) {
        req1.style.color = green
    } else {
        req1.style.color = red
        en = false
    }

    if (-160 <= lons && lons <= -60 && -160 <= lone && lone <= -60) {
        req2.style.color = green
    } else {
        req2.style.color = red
        en = false
    }

    if (bmin <= bmax) {
        req3.style.color = green
    } else {
        req3.style.color = red
        en = false
    }

    req4L.style.color = green
    req4M.style.color = green
    req4R.style.color = green
    if (llmin > (bmax - bmin) * r) {
        req4L.style.color = red
        req4M.style.color = red
        en = false
    } else if ((bmax - bmin) * r > 700) {
        req4M.style.color = red
        req4R.style.color = red
        en = false
    }

    submitButton.disabled = !en
}

auto1.addEventListener('click', doAuto1)
auto1.addEventListener('click', updateRequirements)
auto2.addEventListener('click', doAuto2)
auto2.addEventListener('click', updateRequirements)

link(minLegLengthSlider, minLegLengthInput)
link(evRangeSlider, evRangeInput)
link(minBatterySlider, minBatteryInput)
link(maxBatterySlider, maxBatteryInput)
link(startBatterySlider, startBatteryInput)

requirementsListen(startLon)
requirementsListen(startLat)
requirementsListen(endLat)
requirementsListen(endLon)
requirementsListen(minLegLengthSlider)
requirementsListen(minLegLengthInput)
requirementsListen(evRangeSlider)
requirementsListen(evRangeInput)
requirementsListen(minBatterySlider)
requirementsListen(minBatteryInput)
requirementsListen(maxBatterySlider)
requirementsListen(maxBatteryInput)
requirementsListen(startBatterySlider)
requirementsListen(startBatteryInput)

updateRequirements()