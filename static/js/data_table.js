let currentData = ''

document.addEventListener("DOMContentLoaded", function () {
    const tableTitle = document.querySelector('#table-title');
    const tableBody = document.querySelector('#table-body');
    const alertDiv = document.querySelector('#alertDiv');
    const roleInfo = document.querySelector('#role-info')

    let sorted_by = ''
    let ascendingSort = true;


    function sortData(arr, property, ascending = true) {
        //Sorts an array of objects based upon a property in the object, currently set to enable a user to sort data by column headers in booking_table.html
        return arr.sort((a, b) => {
            sorted_by = property
            let valueA = a[property];
            let valueB = b[property];

            // Convert strings to lowercase to ensure case-insensitive comparison
            if (typeof valueA === 'string') valueA = valueA.toLowerCase();
            if (typeof valueB === 'string') valueB = valueB.toLowerCase();

            // For date comparison, convert to Date objects
            if (property.includes('time')) {
                valueA = new Date(valueA);
                valueB = new Date(valueB);
            }

            if (valueA < valueB) return ascending ? -1 : 1;
            if (valueA > valueB) return ascending ? 1 : -1;
            return 0;
        });
    }

    function manageAlerts(message, type) {
        // Used in combination with bootstrap alerts, displays the message to the user in an alert with the color of type 'success' = green, 'warning' =yellow, 'danger' = red
        let html = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert" >
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
        `
        alertDiv.innerHTML = html
    }

    async function getBookedNotComplete() {
        //API call to get data for the table, pass it to sortData function then returns the sorted Data
        const response = await axios.get('/get_booked_not_complete');
        let sortedData = sortData(response.data, 'origin_name');
        currentData = sortedData;
        return sortedData;
    };

    async function getCompanyBookings() {
        //API call to get data for the table, pass it to sortData function then returns the sorted Data
        const id = roleInfo.getAttribute('data-company')
        const response = await axios.get(`/get_company_bookings/${id}`)
        let sortedData = sortData(response.data, 'driver_name')
        currentData = sortedData;
        return sortedData;
    }

    async function getDriverId() {
        //API call to get driver id for the getMyBookings function.
        const response = await axios.get('/driver_id')
        return response.data
    }

    async function getMyBookings() {
        //API call to get data for the table, pass it to sortData function then returns the sorted Data
        const response = await getDriverId()
        id = response.message
        if (id) {
            const response = await axios.get(`/get_my_bookings/${id}`)
            let sortedData = sortData(response.data, 'appointment_time')
            currentData = sortedData;
            return sortedData;
        } else {
            const message = "Driver id not found, please try again"
            manageAlerts(message, 'warning')
        }


    }

    const functionMap = {
        // Object to map the API function calls to load the correct data based upon a user's role.
        'Planner': getBookedNotComplete,
        'Hub_Manager': getBookedNotComplete,
        'Dispatcher': getCompanyBookings,
        'Driver': getMyBookings
    }

    const timezones = {
        //Object to map the time zones needed for convertTime function.
        'ET': 'America/New_York',
        'CT': 'America/Chicago',
        'MT': 'America/Denver',
        'PT': 'America/Los_Angeles',
        'AZ': 'America/Phoenix'
    }

    function convertTime(tz, utcDt) {
        //Converts the UTC time sent by the API to the local timezone for the location being viewed. 
        const utcDate = new Date(utcDt);
        const convertedDate = utcDate.toLocaleString('en-US', { timeZone: timezones[tz], month: 'numeric', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
        return convertedDate;
    }

    function genHtml(arr) {
        //Takes an array of objects from the API response and formats it to a table row returns the html to the caller. 
        let html = ''

        arr.forEach(item => {
            let row = `
            <tr>
              <td>${item.origin_name}</td>
              <td>${item.delivery_name}</td>
              <td>${convertTime(item.origin_timezone, item.appointment_time)}</td>
              <td>${item.company_name}</td>
              <td>${item.driver_name}</td>
              <td>${item.notes}</td>
              <td>${item.is_planned ? 'Yes' : 'No'}</td>
              <td>${!item.is_planned && !item.is_complete && item.status != 'cancelled' && item.delivery_name != 'Delivery Only' ? `<small><button class="btn btn-sm btn-success planned" data-id="${item.id}">Load Planned</button></small>` : ''}</td>
              <td>${item.is_complete == 'True' ? 'Yes' : 'No'}</td>
              <td>${!item.is_complete && item.status != 'cancelled' ? `<small><button class="btn btn-sm btn-success complete" data-id="${item.id}">Complete</button></small>` : ''}</td>
              <td>${item.status}</td>
              <td>${item.status != 'cancelled' && item.status != 'completed' ? `<small><button class="btn btn-sm btn-danger cancel" data-id="${item.id}">Cancel</button></small>` : ''}</td>
              <td>${item.created_by}</td>
              <td>${convertTime(item.origin_timezone, item.booking_time)}</td>
            </tr>
             
              `
            html += row;
        })

        return html

    };


    async function loadPage(func) {
        // Based upon the user's role in the functionMap, the function is passed in. That function returns an array of objects from the API call. That array of objects is passed
        // to genHtml to generate the html for the table with the data from the API call. Table is updated to the DOM

        let data = await func();

        html = genHtml(data);
        tableBody.innerHTML = html

    };

    function start() {
        //Determines the user's role and calls the functionMap to determine the appropriate function to use, that function is passed to loadPage. 
        const role = roleInfo.getAttribute('data-role')
        const func = functionMap[role]
        if (typeof func === "function") {
            loadPage(functionMap[role])
        } else {
            console.error("Function not found for role", role);
        }

    }

    start()

    async function appointmentApiHandler(id, type) {
        //REST API calls to update the status of bookings in the database, id = booking.id, type chooses the API call made
        // 'planned' updates db booking.status to planned and booking.is_planned = true
        // 'cancel' updates db booking.status to cancelled and appointment_slot.is_booked = false
        // 'complete' updates db booking.status to complete and booking.is_complete = true 
        if (type == 'planned') {
            let response = await axios.post(`/is_planned/${id}`)

            if (response.data.message) {
                manageAlerts(response.data.message, 'success')
            }
        }

        if (type == 'cancel') {
            let response = await axios.post(`/cancel/${id}`)

            if (response.data.message) {
                manageAlerts(response.data.message, 'success')
            }
        }

        if (type == 'complete') {
            let response = await axios.post(`/completed/${id}`)

            if (response.data.message) {
                manageAlerts(response.data.message, 'success')
            }
        }
    }

    document.querySelectorAll('.table th').forEach(header =>
        header.addEventListener("click", () => {
            //Click event listener for the table headers to trigger the sort functions and update table with sorted data. 
            const property = header.getAttribute('data-property')
            if (property == sorted_by) {
                ascendingSort = !ascendingSort
            }
            else {
                sorted_by = property
            }
            const sortedData = sortData(currentData, property, ascendingSort)
            currentData = sortedData
            html = genHtml(sortedData)
            tableBody.innerHTML = html
        }))

    document.body.addEventListener('click', function (e) {
        if (e.target && e.target.matches('.planned')) {
            //Click event listener for the load planned buttons, updates table to represent the changes to the database on REST API call. 
            const plannedTd = e.target.offsetParent.previousElementSibling;
            const row = e.target.offsetParent.parentElement;
            const statusTd = row.children[10];
            const bookingId = e.target.getAttribute('data-id')
            appointmentApiHandler(bookingId, 'planned')
            e.target.classList.add('d-none')
            plannedTd.innerText = 'Yes'
            statusTd.innerText = 'planned'
        }
    })

    document.body.addEventListener('click', function (e) {
        if (e.target && e.target.matches('.complete')) {
            //Click event listener for the complete buttons, updates table to represent the changes to the database on REST API call.
            const completedTd = e.target.offsetParent.previousElementSibling;
            const row = e.target.offsetParent.parentElement;
            const statusTd = row.children[10];
            const bookingId = e.target.getAttribute('data-id')
            appointmentApiHandler(bookingId, 'complete')
            completedTd.innerText = 'Yes'
            e.target.classList.add('d-none')
            statusTd.innerText = 'completed'
        }
    })

    document.body.addEventListener('click', function (e) {
        if (e.target && e.target.matches('.cancel')) {
            //Click event listener for the cancel buttons, updates table to represent the changes to the database on REST API call.
            const completedTd = e.target.offsetParent.previousElementSibling;
            const row = e.target.offsetParent.parentElement;
            const statusTd = row.children[10];
            const bookingId = e.target.getAttribute('data-id')
            appointmentApiHandler(bookingId, 'cancel')
            e.target.classList.add('d-none')
            completedTd.innerText = 'Yes'
            statusTd.innerText = 'cancelled'
        }
    })



})




