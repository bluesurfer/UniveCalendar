/* initialize map
 -----------------------------------------------------------------*/
function initialize() {
    var mapCanvas = document.getElementById('map');
    var mapOptions = {
        center: new google.maps.LatLng(45.435, 12.335),
        zoom: 14,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };

    var map = new google.maps.Map(mapCanvas, mapOptions);
    window.markers = [];

    function showMark(marker) {
        if (window.currentMarker) {
            window.currentMarker['polyline'].setVisible(false);
            window.currentMarker['info'].close();
        }

        marker['polyline'].setVisible(true);
        marker['info'].open(map, marker);

        map.setZoom(18);
        map.panTo(marker.position);

        window.currentMarker = marker;
    }

    $.ajax({
        url: $SCRIPT_ROOT + '/api/users/' + $USER_ID + '/locations/',
        dataType: 'json',
        success: function (json) {
            for (var i = 0; i < json.locations.length; i++) {
                var loc = json.locations[i];

                // Add a marker for this location.
                var marker = new google.maps.Marker({
                    position: new google.maps.LatLng(loc.lat, loc.lng),
                    map: map,
                    animation: google.maps.Animation.DROP,
                    title: loc.name
                });

                var contentString = '<div id="content">' +
                    '<div id="siteNotice">' +
                    '</div>' +
                    '<h1 id="firstHeading" class="firstHeading">' + loc.name + '</h1>' +
                    '<div id="bodyContent">' +
                    '<p>' + loc.address + '</p>' +
                    '<p>Lezioni in: ' + loc.classrooms + '</p>' +
                    '</div>' +
                    '</div>';

                marker['info'] = new google.maps.InfoWindow({
                    content: contentString
                });

                // Construct the polygon.
                if (loc.polyline) {
                    marker['polyline'] = new google.maps.Polygon({
                        paths: google.maps.geometry.encoding.decodePath(loc.polyline),
                        strokeColor: '#FF0000',
                        strokeOpacity: 0.8,
                        strokeWeight: 3,
                        fillColor: '#FF0000',
                        fillOpacity: 0.35
                    });
                    marker['polyline'].setVisible(false);
                    marker['polyline'].setMap(map);
                }

                google.maps.event.addListener(marker, 'click', function () {
                    showMark(this);
                });

                window.markers[loc.id] = marker;
            }
        }
    });
}

google.maps.event.addDomListener(window, 'load', initialize);

