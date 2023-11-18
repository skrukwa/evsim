const version = 'weekly'
const KEY = '65_73_122_97_83_121_66_112_104_72_57_120_68_114_105_109_103_101_100_75_79_82_118_105_50_74_99_90_116_66_84_67_52_122_65_49_70_73_119'
function get_key() {return String.fromCharCode(...KEY.split('_'))}

(g=>{var h,a,k,p="The Google Maps JavaScript API",c="google",l="importLibrary",q="__ib__",m=document,b=window;b=b[c]||(b[c]={});var d=b.maps||(b.maps={}),r=new Set,e=new URLSearchParams,u=()=>h||(h=new Promise(async(f,n)=>{await (a=m.createElement("script"));e.set("libraries",[...r]+"");for(k in g)e.set(k.replace(/[A-Z]/g,t=>"_"+t[0].toLowerCase()),g[k]);e.set("callback",c+".maps."+q);a.src=`https://maps.${c}apis.com/maps/api/js?`+e;d[q]=f;a.onerror=()=>h=n(Error(p+" could not load."));a.nonce=m.querySelector("script[nonce]")?.nonce||"";m.head.append(a)}));d[l]?console.warn(p+" only loads once. Ignoring:",g):d[l]=(f,...n)=>r.add(f)&&u().then(()=>d[l](f,...n))})
({key:get_key(),v:version,})

async function initMap() {

    const { LatLng } = await google.maps.importLibrary('core')
    const { Map, Polyline, InfoWindow } = await google.maps.importLibrary('maps')
    const { AdvancedMarkerElement } = await google.maps.importLibrary('marker')

    const map = new Map(document.getElementById('map'), {
        zoom: 5,
        center: { lat: 39.784305, lng: -101.372835 },
        mapTypeId: 'terrain',
        mapId: 'DEMO_MAP_ID'
    })

    let coords = []
    for (let leg of data['legs_summary']) {
        for (let coord of leg['polyline']) {
            coords.push(new LatLng(coord[0], coord[1]))
        }
    }
    const polyline = new Polyline({
        path: coords,
        geodesic: true,
        strokeColor: '#FF0000',
        strokeOpacity: 1.0,
        strokeWeight: 2,
    })
    polyline.setMap(map)

    for (let leg of data['legs_summary']) {
        const cs = leg['charge_station']

        const marker = new AdvancedMarkerElement({
            map: map,
            position: new LatLng(cs['latitude'], cs['longitude']),
            title: cs['name']
        })
        const infowindow = new InfoWindow({
            content: `
                <b>name:</b> ${cs['name']}<br>
                <b>address:</b> ${cs['address']}<br>
                <b>hours:</b> ${cs['hours']}<br>
                <b>phone:</b> ${cs['phone']}<br>
                <b>open date:</b> ${cs['open_date']}<br>
            `
        })
        marker.addListener('click', () => {
            infowindow.open({map: map, anchor: marker})
        })

    }

    const last = data['destination_summary']['charge_station']

    marker = new google.maps.Marker({
        map: map,
        position: new LatLng(last['latitude'], last['longitude']),
        title: last['name']
    })
    const infowindow = new InfoWindow({
        content: `
            <b>name:</b> ${last['name']}<br>
            <b>address:</b> ${last['address']}<br>
            <b>hours:</b> ${last['hours']}<br>
            <b>phone:</b> ${last['phone']}<br>
            <b>open date:</b> ${last['open_date']}<br>
        `
    })
    marker.addListener('click', () => {
        infowindow.open({map: map, anchor: marker})
    })

}
  
initMap()