// Jitenshea functions for the 'station' page

// Station summary
$(document).ready(function() {
  var station_id = document.getElementById("stationSummary").dataset.stationId;
  $.get(API_URL + "/lyon/stations/" + station_id, function (content) {
    var station = content.data[0];
    $("#titlePanel").append("#" + station.id + " " + station.name + " in " + station.city);
    $("#id").append(station.id);
    $("#name").append(station.name);
    $("#nbStands").append(station.nb_stands);
    $("#address").append(station.address);
    $("#city").append(station.city);
  } );
} );

// Get the station ID from the URL /lyon/stations/ID
function stationIdFromURL() {
  var path = window.location.pathname;
  var elements = path.split('/')
  return parseInt(elements[elements.length -1]);
}

// Map centered to the station
function stationsMap(map, data) {
  var OSM_Mapnik = L.tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    {
      maxZoom: 19,
      attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }
  );
  OSM_Mapnik.addTo(map);
  // The center of the map is the station coords
  var station_id = stationIdFromURL();
  var station = data.features.filter(feature => feature.properties.id == station_id);
  map.setView([station[0].geometry.coordinates[1],
               station[0].geometry.coordinates[0]], 16);
  L.geoJSON(data, {
    pointToLayer: function(geoJsonPoint, latlng) {
      var marker = null;
      if (geoJsonPoint.properties.id == station_id) {
        marker = L.marker(latlng);
      } else {
        marker = L.circleMarker(latlng, {radius: 5});
      }
      // Popup with ID and name.
      marker.bindPopup("<ul><li><b>ID</b>: " + geoJsonPoint.properties.id
                       + "</li><li><b>Name</b>: " + geoJsonPoint.properties.name + "</li></ul>")
        .on('mouseover', function(e) {
          this.openPopup();
        })
        .on('mouseout', function(e) {
          this.closePopup();
        });
      return marker;
    }
  }).addTo(map);
};

// Map centered to the station with Leaflet
$(document).ready(function() {
  var station_map = L.map("stationMap");
  var city = document.getElementById("stationMap").dataset.city;
  $.get(API_URL + "/lyon/availability?geojson=true", function(data) {
    console.log("stations geodata GET request in " + city);
    stationsMap(station_map, data);
    sessionStorage.setItem(city, JSON.stringify(data));
  } );
} );

// Timeseries plot
$(document).ready(function() {
  var station_id = document.getElementById("stationTimeseries").dataset.stationId;
  // Only plot seven days.
  var stop = new Date();
  var start = new Date(stop);
  stop.setDate(stop.getDate() + 1);
  start.setDate(start.getDate() - 7);
  start = start.toISOString().substring(0, 10);
  stop = stop.toISOString().substring(0, 10);
  var url = API_URL + "/lyon/timeseries/" + station_id + "?start=" + start + "&stop=" + stop;
  $.get(url, function(content) {
    // just a single station
    var data = content.data[0];
    var station_name = data.name;
    var date = data.ts;
    var bikes = date.map(function(t, i) {
      return [Date.parse(t), data.available_bikes[i]];
    });
    Highcharts.stockChart('stationTimeseries', {
      // use to select the time window
      rangeSelector: {
        buttons: [{
          type: 'day',
          count: 1,
          text: '1D'
        }, {
          type: 'all',
          count: 1,
          text: 'All'
        }],
        selected: 0,
        inputEnabled: false
      },
      legend:{
	align: 'center',
	verticalAlign: 'top',
	enabled: true
      },
      title: {
        text: 'Timeseries for the station ' + station_name
      },
      yAxis: {
        title: {
          text: 'Number of items'
        }
      },
      xAxis: {
        type: "datetime"
      },
      time: {
	useUTC: false
      },
      series: [{
        name: "bikes",
        data: bikes,
        tooltip: {
          valueDecimals: 1
        }
      }]
    } );
  } );
} );
