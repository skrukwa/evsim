// to handle mobile devices that do not yet support lvh

function onMobile() {
    const mobileWidth = (window.innerWidth <= 750)
    const mobileAspectRatio = ((window.innerWidth / window.innerHeight) <= 3 / 4)
    return mobileWidth && mobileAspectRatio
}

function updateLvh() {
    if (lvh100.offsetHeight / 100 > lvh) {
        lvh = lvh100.offsetHeight / 100
        document.documentElement.style.setProperty('--lvh', lvh + 'px')
    }
}

function lvhHandler() {
    if (onMobile()) {
        updateLvh()
    } else {
        document.documentElement.style.setProperty('--lvh', '1lvh')
        lvh = lvh100.offsetHeight / 100
    }
}

const lvh100 = document.getElementById('lvh100')
let lvh = lvh100.offsetHeight / 100

window.addEventListener('resize', lvhHandler)