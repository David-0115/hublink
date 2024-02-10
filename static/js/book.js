document.addEventListener('DOMContentLoaded', function () {
    const companySelect = document.querySelector('#company-select')
    const driverSelect = document.querySelector('#driver-select')
    const deliveryOnly = document.querySelector('#delivery-only')
    const tripInfo = document.querySelector('#trip-info')
    const destination = document.querySelector('#destination')
    const loc1IdTag = document.querySelector('#loc1_id')
    const slotIdTag = document.querySelector('#slot_id')
    const mapOriginName = document.querySelector('#map-origin-name')
    const mapDestinationName = document.querySelector('#map-destination-name')
    const tripMiles = document.querySelector('#trip-miles')
    const travelTime = document.querySelector('#travel-time')
    const loadMsg = document.querySelector('#load-msg')
    const mapDiv = document.querySelector('#map')
    const mapDest = document.querySelector('#map-dest')
    const mapMiles = document.querySelector('#map-miles')
    const mapTravel = document.querySelector('#map-travel')
    const truckSettings = document.querySelector('#truck-settings')
    const bingEULA = document.querySelector('#bing-eula')
    const roleInfo = document.querySelector('#role-info')

    async function getDrivers(companyId) {
        //REST API call to get drivers based upon companyId, used with loadDrivers.
        response = await axios.get(`/get-drivers/${companyId}`)
        driverData = response.data

        return (driverData)
    }

    async function loadDrivers(companyId) {
        //Calls getDrivers to get a companies drivers based upon user company selection, adds drivers to <select> tags and updates the DOM.
        let data = await getDrivers(companyId)

        let html = '<option value="">Select One...</option>'
        data.forEach(obj => {
            for (let k in obj) {
                html += `<option value="${k}"> ${obj[k]} </option>`
            }
        });
        if (driverSelect) {
            driverSelect.innerHTML = html;
            driverSelect.required = true;
        }
    }

    if (roleInfo.getAttribute('data-role') == 'Dispatcher') {
        //Dispatchers can only view drivers from their company, this gets the company id from the data tag and calls loadDrivers
        const companyId = companySelect.value
        loadDrivers(companyId)
    }

    function isDriverOptions() {
        //Determines if there are existing driver options in the DOM, returns Bool. 
        const html = driverSelect.innerHTML
        if (!html.includes('<option')) {
            return false
        }
        return true
    }

    companySelect.addEventListener("change", function (e) {
        //Event listener for a user changing the Company selection to trigger drivers to be loaded to the DOM
        let options = isDriverOptions()
        if (!options) {
            const companyId = (e.target.value)
            loadDrivers(companyId)
        }

    })

    deliveryOnly.addEventListener("change", function (e) {
        // If the shipment is a delivery only it does not have a destination.
        // If deliveryOnly box is checked this function removes destination and map items from the DOM.
        let formElements = document.querySelectorAll('.apt-form');

        if (deliveryOnly.checked === true) {

            for (let div of formElements) {
                if (div.childNodes[1] && div.childNodes[1].innerHTML.includes("Destination:")) {
                    div.classList.add('d-none');
                    tripInfo.classList.add('d-none');
                };
            };
        };

        if (deliveryOnly.checked === false && tripInfo.classList.contains('d-none')) {

            for (let div of formElements) {
                if (div.childNodes[1] && div.childNodes[1].innerHTML.includes("Destination:")) {
                    div.classList.remove('d-none');
                    tripInfo.classList.remove('d-none');
                };
            };
        };

    });

    let map;
    let mapState = false;

    function loadMap(data) {
        //Uses data passed in from server BingMaps api call then
        //Loads the map to the DOM, uses route coordinates to create the routeline based upon coordinates for origin and destination. 

        const loc1Coords = loc1IdTag.getAttribute('data-coords').split(',').map(Number);

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


    destination.addEventListener("change", function (e) {
        //Event Listener for the destination field, when it is selected it triggers:
        //DOM show - Trip data headers (filled in by loadMap)
        //showMap API call with origin, destination and appointment id

        const loc1Id = loc1IdTag.getAttribute('data-loc1')
        const loc2Id = e.target.value
        const slotId = slotIdTag.getAttribute('data-slot')

        loadMsg.classList.add('d-none')

        const dNone = [mapOriginName, mapDestinationName, tripMiles, travelTime, mapDiv, truckSettings, bingEULA]
        dNone.forEach(element => {
            element.classList.remove('d-none')
        });

        if (mapState && map) {
            map.remove();
            mapState = false;
            const clearValues = [mapDest, mapMiles, mapTravel]
            clearValues.forEach(element => {
                element.innerText = '';
            });
        };

        mapDest.innerText = destination.options[destination.selectedIndex].innerText

        showMap(loc1Id, loc2Id, slotId)
    })


});




