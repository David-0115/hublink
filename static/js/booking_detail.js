document.addEventListener("DOMContentLoaded", function () {
    const loadMsg = document.querySelector('#load-msg');
    const mapDiv = document.querySelector('#map');
    const mapDest = document.querySelector('#map-dest');
    const mapMiles = document.querySelector('#map-miles');
    const mapTravel = document.querySelector('#map-travel');
    const truckSettings = document.querySelector('#truck-settings');
    const bingEULA = document.querySelector('#bing-eula');
    const slotId = document.querySelector('#slot_id');
    const destId = document.querySelector('#destId');
    const loc1Id = document.querySelector('#loc1_id');
    const cancel = document.querySelector('#cancel');
    const planned = document.querySelector('#planned');
    const complete = document.querySelector('#complete');
    const bookId = document.querySelector('#bookId');
    const plannedBool = document.querySelector('#plannedBool');
    const completeBool = document.querySelector('#completeBool');
    const status = document.querySelector('#status');
    const cancelDiv = document.querySelector('#cancelDiv');
    const mapOriginDiv = document.querySelector('#map-origin-name');
    const mapDestinationDiv = document.querySelector('#map-destination-name');
    const mapTripMilesDiv = document.querySelector('#trip-miles');
    const mapTravelTimeDiv = document.querySelector('#travel-time');


    let map;
    let mapState = false;

    function loadMap(data) {
        //Uses data passed in from server BingMaps api call then
        //Loads the map to the DOM, uses route coordinates to create the routeline based upon coordinates for origin and destination. 

        const loc1Coords = loc1Id.getAttribute('data-coords').split(',').map(Number);

        map = L.map('map').setView(loc1Coords, 9)

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);

        const routeCoordinates = data[0].routePath;

        const originMarker = L.marker(data[0].startLocation.coordinates).addTo(map).bindPopup(`${data[0].startLocation.address}`)
        const destMarker = L.marker(data[0].endLocation.coordinates).addTo(map).bindPopup(`${data[0].endLocation.address}`)
        const routeLine = L.polyline(routeCoordinates, { color: 'blue' }).addTo(map);
        map.fitBounds(routeLine.getBounds());
        mapMiles.innerText = data[0].totalDistance.toFixed(1);
        mapTravel.innerText = data[0].travelTimeTraffic;

        map.invalidateSize()
        mapState = true
    };



    async function showMap(loc1, loc2, slot) {
        //API call to server to call BingMaps and parse the data, parsed data is returned as response.
        //response.data (array of objects) is passed to loadMap displaying the map.        
        url = `/get_map_data/${loc1}/${loc2}/${slot}`
        response = await axios.get(url)
        loadMap(response.data)

    }

    const dest = destId.getAttribute('data-loc2');
    if (dest !== "DO") {
        //Conditional - if Destination is not delivery only then this unhides the map and trip information for display on the DOM.
        const unhide = [mapOriginDiv, mapDestinationDiv, mapTripMilesDiv, mapTravelTimeDiv, mapDiv, mapDest, mapMiles, mapTravel, truckSettings, bingEULA]
        const loc1 = loc1Id.getAttribute('data-loc1');
        const loc2 = dest;
        const slot = slotId.getAttribute('data-slot');
        unhide.forEach(element => element.classList.remove('d-none'));
        loadMsg.classList.add('d-none')

        showMap(loc1, loc2, slot)

    }



    const bookingId = bookId.getAttribute('data-bookId')
    if (planned) {
        //If planned button exists, adds event listener for click to call REST API that updates the booking status to planned. 
        planned.addEventListener("click", async function () {

            const response = await axios.post(`/is_planned/${bookingId}`)

            if (response.data.message) {
                planned.classList.add('d-none');
                plannedBool.innerText = "True";
                status.innerText = "Planned"
            }
        })
    }

    if (complete) {
        //If complete button exists, adds event listener for click to call REST API that updates the booking status to complete.
        complete.addEventListener("click", async function () {

            const response = await axios.post(`/completed/${bookingId}`)

            if (response.data.message) {
                complete.classList.add('d-none');
                cancelDiv.classList.add('d-none');
                completeBool.innerText = "True";
                status.innerText = "Complete";
            }
        })
    }

    if (cancel) {
        //If cancel button exists, adds event listener for click to call REST API that updates the booking status to cancelled.
        cancel.addEventListener("click", async function () {

            const response = await axios.post(`/cancel/${bookingId}`)

            if (response.data.message) {
                cancelDiv.classList.add('d-none');
                status.innerText = "Canceled";
                planned.classList.add('d-none')
                complete.classList.add('d-none')
            }
        })
    }


})

