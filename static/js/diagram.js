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

    const currencies = [];
    const balances = [];
    const colors = [];

    for (item in balancesData) {
        var currency = balancesData[item];

        currencies.push(currency.currency);
        balances.push(currency.notionalBalance);
        colors.push(getColor(currency.currency));
    }

    var chart = new Chart(chartCanvas, {
        type: "doughnut",
        data: {
            labels: currencies,
            datasets: [{
                label: 'Balance',
                data: balances,
                backgroundColor: colors
            }]
        },
        options: {
            cutout: "50%"
        }
    });
}


function getColor(currency) {
    var color;

    switch (currency) {
        case "BAT":
            color = "rgba(235,95,0,100)";
            break;
        case "BCH":
            color = "rgba(110,190,60,100)"
            break;
        case "BTC":
            color = "rgba(250,200,10,100)";
            break;
        case "ETH":
            color = "rgba(85,110,235,95)";
            break;
        case "LTC":
            color = "rgba(185,180,180,100)"
            break;
        case "SHIB":
            color = "rgba(240,170,10,95)";
            break;
        case "SLP":
            color = "rgba(235,110,165,95)";
            break;
        case "USD":
            color = "rgba(100,100,100,40)";
            break;
        case "ZEC":
            color = "rgba(250,220,80,100)";
            break;
        default:
            color = "rgba(0,0,0,0)";
    }

    return color;
}