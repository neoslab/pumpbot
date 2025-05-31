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
            console.error("Error:", error);
            showToast("Server error", 'error');
        });
    }

    // Update bot status block and buttons
    function refreshBotStatus() 
    {
        $.get('/api/botstatus', function(data) 
        {
            $('#botAPImessage').text(data.label);
            $('#botStatus').removeClass('text-success text-danger').addClass(data.css);
        }).fail(function(xhr) 
        {
            console.error("Bot status fetch failed:", xhr.responseText);
        });
    }

    function refreshBotBalance() 
    {
        $.get('/api/botbalance', function(data) 
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
        $('[name="main.name"]').val($(this).val());
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
        $.post('/api/botstart', function(data)
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
            console.error("Start bot error:", xhr.responseText);
            showToast('Failed to start bot', 'error');
        });
    });

    // Stop bot
    $('#stopBot').click(function() 
    {
        $.post('/api/botstop', function(data) 
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
            console.error("Stop bot error:", xhr.responseText);
            showToast('Failed to stop bot', 'error');
        });
    });

    // Auto-refresh status every 5s
    setInterval(refreshBotStatus, 5000);
    setInterval(refreshBotBalance, 5000);
});