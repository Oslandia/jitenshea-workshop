// Jitenshea functions for the 'city' page

// Map with all stations with Leaflet
$(document).ready(function() {
  var tile = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  });
  var city = document.getElementById("stationMap").dataset.city;
  var map = L.map("stationMap");
  var currentLayer = L.geoJSON(null, {
    style: function(data) {
      return {
	color: d3.interpolateRdYlGn(
	  data.properties.nb_bikes / data.properties.nb_stands
	)
      }
    },
    pointToLayer: function(data, coords) {
      return L.circleMarker(coords, {radius: 4})
	.bindPopup("<ul><li><b>ID</b>: " + data.properties.id
		   + "</li><li><b>Name</b>: " + data.properties.name
		   + "</li><li><b>Stands</b>: " + data.properties.nb_stands
		   + "</li><li><b>Bikes</b>: " + data.properties.nb_bikes
		   + "</li><li><b>At</b> " + data.properties.timestamp + "</li></ul>")
	.on('mouseover', function(e) {
	  this.openPopup();
	})
	.on('mouseout', function(e) {
	  this.closePopup();
	})
	.on('click', function(e) {
	  window.location.assign(city + "/" + data.properties.id);
	});
    }
  }).addTo(map);
  var clusterLayer = L.geoJSON(null, {
    style: function(data){
      return {color: d3.schemeSet1[data.properties.cluster_id]};
    },
    pointToLayer: function(data, coords) {
      return L.circleMarker(coords, {radius: 4})
	.bindPopup("<ul><li><b>ID</b>: " + data.properties.id
		   + "</li><li><b>Name</b>: " + data.properties.name + "</li>"
		   + "<li><b>Cluster id</b>: " + data.properties.cluster_id + "</li></ul>")
	.on('mouseover', function(e) {
	  this.openPopup();
	})
	.on('mouseout', function(e) {
	  this.closePopup();
	})
	.on('click', function(e) {
	  window.location.assign(city + "/" + data.properties.id);
	});
    }
  });
  var baseMaps = {
    "current": currentLayer,
    "cluster": clusterLayer
  };
  tile.addTo(map);
  L.control.layers(baseMaps).addTo(map);
  $.getJSON(API_URL + "/" + city + "/availability?geojson=true", function(data) {
    currentLayer.addData(data);
    map.fitBounds(currentLayer.getBounds())
  });
  $.getJSON(API_URL + "/" + city + "/clusters?geojson=true", function(data) {
    clusterLayer.addData(data);
  });
});

// K-mean centroid plotting
$(document).ready(function() {
  var url = API_URL + "/lyon/centroids";
  $.get(url, function(content) {
    function mapCentroidValues(id){
      return content.data[id].hour.map(function(t, i){
	return [t, content.data[id].values[i]];
      });
    };
    var clusters = {};
    for (cluster = 0; cluster <= 3; cluster++)
      clusters[content.data[cluster].cluster_id] = mapCentroidValues(cluster)
    Highcharts.chart('clusterCentroids', {
      title: {
        text: 'Cluster centroid definitions'
      },
      yAxis: {
        title: {
          text: 'Available bike percentage'
        }
      },
      xAxis: {
        type: "Hour of the day"
      },
      colors: d3.schemeSet1,
      series: [{
        name: "cluster 0",
        data: clusters[0],
        tooltip: {
          valueDecimals: 2
        }
      },{
        name: "cluster 1",
        data: clusters[1],
        tooltip: {
          valueDecimals: 2
        }
      },{
        name: "cluster 2",
        data: clusters[2],
        tooltip: {
          valueDecimals: 2
        }
      },{
        name: "cluster 3",
        data: clusters[3],
        tooltip: {
          valueDecimals: 2
        }
      }]
    } );
  } );
} );
