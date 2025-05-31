$(document).ready(function() 
{
    // CSRF token for all AJAX requests
    $.ajaxSetup(
    {
        headers: 
        {
            'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
        }
    });

    // Toast notification
    function showToast(message, type = 'success') 
    {
        const toast = document.getElementById("toast");
        toast.className = "show " + type;
        toast.textContent = message;
        setTimeout(() => 
        {
            toast.className = toast.className.replace("show", "");
        }, 1500);
    }

    // Toggle visibility of bot-specific fields
    function toggleBotFields() 
    {
        const botstatus = $('[name="main.status"]').val();
        $('.bot-fields').toggle(botstatus === "True");
    }

    // Toggle advanced bot parameters based on form logic
    function toggleChangeFields() 
    {
        const botstatus = $('[name="main.status"]').val();
        const sandbox = $('[name="main.sandbox"]').val();
        const fastmode = $('[name="trade.fastmode"]').val();
        const holderscheck = $('[name="rules.holderscheck"]').val();
        const trailprofit = $('[name="trade.trailprofit"]').val();

        $('[name="main.initbalance"]').closest('.mb-3').toggle(botstatus === "True" && sandbox === "True");
        $('[name="trade.fasttokens"]').closest('.mb-3').toggle(fastmode === "True");
        $('[name="rules.holdersbalance"]').closest('.mb-3').toggle(holderscheck === "True");

        const trailFields = [
            'trade.trailone',
            'trade.trailtwo',
            'trade.trailthree',
            'trade.trailfour',
            'trade.trailfive'
        ];
        trailFields.forEach(field => 
        {
            $(`[name="${field}"]`).closest('.mb-3').toggle(trailprofit === "True");
        });
    }

    // Toggle bot switch state from UI
    function toggleBotSwitch(filename, botstatus) 
    {
        fetch('/switch', 
        {
            method: 'POST',
            headers: 
            {
                'Content-Type': 'application/json',
                'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
            },
            body: JSON.stringify(
            {
                filename: filename,
                status: botstatus
            })
        })
        .then(response => 
        {
            if(response.ok) 
            {
                showToast("Your bot configuration has been updated successfully", 'success');
            } 
            else 
            {
                showToast("An unknown error occurred while updating the bot configuration", 'error');
            }
        })
        .catch(error => 
        {
            showToast("Server error", 'error');
        });
    }

    // Update bot status block and buttons
    function refreshBotStatus() 
    {
        $.get('/api/show-status', function(data) 
        {
            $('#botAPImessage').text(data.label);
            $('#botStatus').removeClass('text-success text-danger').addClass(data.css);
        });
    }

    function refreshBotBalance() 
    {
        $.get('/api/show-balance', function(data) 
        {
            $('#botBalance').text(`${data.balance} SOL`);
        });
    }

    // Init bot status display based on BOTSTATUS
    if(BOTSTATUS) 
    {
        $('#StartBotCont').hide();
        $('#StopBotCont').show();
    } 
    else 
    {
        $('#StopBotCont').hide();
        $('#StartBotCont').show();
    }

    // Sync filename with bot name field
    $('[name="filename"]').on('input keyup change', function() 
    {
        $('[name="main.botname"]').val($(this).val());
    });

    // Run toggle logic on page load
    toggleBotFields();
    toggleChangeFields();

    $('[name="main.status"]').on('change', function() 
    {
        toggleBotFields();
        toggleChangeFields();
    });

    $('[name="main.sandbox"], [name="filters.listener"], [name="trade.fastmode"], [name="trade.trailprofit"], [name="rules.holderscheck"]').on('change', toggleChangeFields);

    // Start bot
    $('#startBot').click(function() 
    {
        $.post('/api/start-trade', function(data)
        {
            showToast(data.message, data.success ? 'success' : 'error');
            if(data.success) 
            {
                $('#StartBotCont').hide();
                $('#StopBotCont').show();
                refreshBotStatus();
                refreshBotBalance();
            }
        }).fail(function(xhr) 
        {
            showToast('Failed to start bot', 'error');
        });
    });

    // Stop bot
    $('#stopBot').click(function() 
    {
        $.post('/api/stop-trade', function(data) 
        {
            showToast(data.message, data.success ? 'success' : 'error');
            if (data.success) {
                $('#StopBotCont').hide();
                $('#StartBotCont').show();
                refreshBotStatus();
                refreshBotBalance();
            }
        }).fail(function(xhr) 
        {
            showToast('Failed to stop bot', 'error');
        });
    });

    // Auto-refresh status every 5s
    setInterval(refreshBotStatus, 5000);
    setInterval(refreshBotBalance, 5000);

    // Auto-refresh tokens table every 30 seconds
    setInterval(function() 
    {
        $.get('/api/list-trades', function(data) 
        {
            const tbody = $('#trades-body');
            tbody.empty();

            if(data.length > 0) 
            {
                $('#trades-alert').fadeOut();
            
                tbody.empty();
                data.forEach(trade => 
                {
                    tbody.append(`<tr class="${trade.rowclass}"><td class="text-start">${trade.mint}</td><td class="text-center">${trade.start}</td><td class="text-center">${trade.stop}</td><td class="text-center">${trade.duration}</td><td class="text-end">${trade.open}</td><td class="text-end">${trade.close}</td><td class="text-end">${trade.amount}</td><td class="text-end">${trade.total}</td><td class="text-end">${trade.profit}</td><td class="text-end">${trade.ratio}</td><td class="text-center">${trade.status}</td></tr>`);
                });
            }
            else
            {
                $('#trades-alert').fadeIn();
                tbody.append(`<tr><td class="text-center text-muted" colspan="11">No trades history available yet.</td></tr>`);
            }
        });
    }, 30000);

    setInterval(function() 
    {
        $.get('/api/list-tokens', function(data) 
        {
            const tbody = $('#tokens-body');
            tbody.empty();

            if(data.length > 0) 
            {
                $('#tokens-alert').fadeOut();
                data.forEach(token => 
                {
                    tbody.append(`<tr><td class="text-start">${token.mint}</td><td class="text-start">${token.symbol.toUpperCase()}</td><td class="text-end">${token.price}</td><td class="text-end">${token.liquidity || 'N/A'}</td><td class="text-end">${token.volume}</td><td class="text-end">${token.marketcap || 'N/A'}</td><td class="text-center">${token.created}</td></tr>`);
                });
            } 
            else 
            {
                $('#tokens-alert').fadeIn();
                tbody.append(`<tr><td class="text-center text-muted" colspan="7">No tokens history available yet.</td></tr>`);
            }
        });
    }, 30000);
});