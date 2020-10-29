    <script>
                var options = {
                series: {{stats | safe}},
                chart: {
                    type: 'bar',
                    height: 350,
                    stacked: true,
                    toolbar:
                        {
                            show: true
                        },
                    zoom: {
                        enabled: true
                    }
                },
                responsive: [{
                    breakpoint: 480,
                    options: {
                        legend: {
                            position: 'bottom',
                            offsetX: -10,
                            offsetY: 0
                        }
                    }
                }],
                plotOptions: {
                    bar: {horizontal: false},
                },
            xaxis: {
                type:
                    'datetime',
                    categories:{{giorni | safe}}
                },
                legend: {
                    position: 'right',
                    offsetY: 40
                },
                fill: {
                    opacity: 1
                }
            };

            var chart = new ApexCharts(document.querySelector("#chart"), options);
            chart.render();
        </script>