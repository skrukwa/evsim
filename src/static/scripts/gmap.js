const version = 'weekly'
const KEY = '65_73_122_97_83_121_67_120_112_88_52_68_67_108_80_81_79_54_114_110_103_76_107_97_104_77_121_76_98_106_74_120_75_115_117_76_70_49_56'
function get_key() {return String.fromCharCode(...KEY.split('_'))}

(g=>{var h,a,k,p="The Google Maps JavaScript API",c="google",l="importLibrary",q="__ib__",m=document,b=window;b=b[c]||(b[c]={});var d=b.maps||(b.maps={}),r=new Set,e=new URLSearchParams,u=()=>h||(h=new Promise(async(f,n)=>{await (a=m.createElement("script"));e.set("libraries",[...r]+"");for(k in g)e.set(k.replace(/[A-Z]/g,t=>"_"+t[0].toLowerCase()),g[k]);e.set("callback",c+".maps."+q);a.src=`https://maps.${c}apis.com/maps/api/js?`+e;d[q]=f;a.onerror=()=>h=n(Error(p+" could not load."));a.nonce=m.querySelector("script[nonce]")?.nonce||"";m.head.append(a)}));d[l]?console.warn(p+" only loads once. Ignoring:",g):d[l]=(f,...n)=>r.add(f)&&u().then(()=>d[l](f,...n))})
({key:get_key(),v:version,})

await initMap()

async function initMap() {
    const { LatLng, LatLngBounds } = await google.maps.importLibrary('core')
    const { Map, Polyline, InfoWindow } = await google.maps.importLibrary('maps')
    const { encoding } = await google.maps.importLibrary('geometry')
    const { AdvancedMarkerElement } = await google.maps.importLibrary('marker')

    const map = new Map(document.getElementById('map'), {
        mapId: '1c01e0202602fb92',
        mapTypeControl: false
    })

    const sw = new LatLng(data['bounds']['southwest']['lat'], data['bounds']['southwest']['lng'])
    const ne = new LatLng(data['bounds']['northeast']['lat'], data['bounds']['northeast']['lng'])
    map.fitBounds(new LatLngBounds(sw, ne))

    const polyline1 = new Polyline({
        path: encoding.decodePath(data['polyline']),
        strokeColor: '#e03a3a',
        strokeWeight: 5,
    })
    polyline1.setMap(map)

    const polyline2 = new Polyline({
        path: encoding.decodePath(data['polyline']),
        strokeColor: '#ff9c9c',
        strokeWeight: 3,
    })
    polyline2.setMap(map)

    for (let leg of data['legs_summary']) {
        const cs = leg['charge_station']

        const marker = new AdvancedMarkerElement({
            map: map,
            position: new LatLng(cs['lat'], cs['lng']),
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

    marker = new AdvancedMarkerElement({
        map: map,
        position: new LatLng(last['lat'], last['lng']),
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
