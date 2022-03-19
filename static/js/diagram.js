window.onload = function() {
    var chartCanvas = document.getElementById('balancesChart');
    var balancesTable = document.getElementById('balancesTable');
    var balancesData = [];

    $('#balancesTable tr').each(function(row, tr) {
        balancesData[row] = {
            "currency": $(tr).find('td:eq(0)').text(),
            "notionalBalance": $(tr).find('td:eq(1)').text(),
            "quantity": $(tr).find('td:eq(2)').text()
        }
    });
    balancesData.shift();


    var chart = new Chart(chartCanvas, {
        type: "doughnut",
        data: {
            labels: ["USD", "BTC", "SHIB", "ETH", "BAT", "ZEC", "SLP"],
            datasets: [{
                label: 'Balance',
                data: [balancesData[0].notionalBalance, balancesData[1].notionalBalance, balancesData[2].notionalBalance, balancesData[3].notionalBalance, balancesData[4].notionalBalance, balancesData[5].notionalBalance, balancesData[6].notionalBalance],
                backgroundColor: [
                    'rgba(100,100,100,40)',
                    'rgba(250,200,10,100)',
                    'rgba(240,170,10,95)',
                    'rgba(135,45,235,95)',
                    'rgba(235,95,0,100)',
                    'rgba(245,215,10,100)',
                    'rgba(235,110,165,95)'
                ]
            }]
        },
        options: {
            cutout: "50%"
        }
    });
}