function showToast(message, type = 'success') 
{
    const toast = document.getElementById("toast");
    toast.className = "show " + type;
    toast.textContent = message;
    setTimeout(() => 
    {
        toast.className = toast.className.replace("show", "");
    }, 500);
}

function toggleBotFields() 
{
    const enabled = $('[name="main.enabled"]').val();
    if(enabled === "True") 
    {
        $('.bot-fields').show();
    } 
    else 
    {
        $('.bot-fields').hide();
    }
}

function toggleBotSwitch(filename, enabled) 
{
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    fetch('/switch', 
    {
        method: 'POST',
        headers: 
        {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(
        {
            filename: filename,
            enabled: enabled
        })
    }).then(response => 
    {
        if(response.ok) 
        {
            showToast("Your bot configuration has been updated successfully", 'success');
        } 
        else 
        {
            showToast("An unknown error occurred while updating the bot configuration", 'error');
        }
    }).catch(error => 
    {
        console.error("Error:", error);
        showToast("Server error", 'error');
    });
}

function toggleConditionalFields() 
{
    const listener = $('[name="filters.listener"]').val();
    const fastmode = $('[name="trade.fastmode"]').val();
    const trailingstop = $('[name="trade.trailingstop"]').val();
    const filteroff = $('[name="filters.filteroff"]').val();

    if(listener === "geyser") 
    {
        $('.geyser-fieldset').removeClass("d-none");
    } 
    else 
    {
        $('.geyser-fieldset').addClass("d-none");
    }

    if(fastmode === "True") 
    {
        $('[name="trade.fasttokens"]').closest('.mb-3').show();
    } 
    else 
    {
        $('[name="trade.fasttokens"]').closest('.mb-3').hide();
    }

    if(trailingstop === "True") 
    {
        $('[name="trade.trailingdrop"]').closest('.mb-3').show();
    } 
    else 
    {
        $('[name="trade.trailingdrop"]').closest('.mb-3').hide();
    }

    const readonlyFields = [
        'filters.matchstring',
        'filters.useraddress',
        'filters.noshorting',
        'timing.tokenmaxage',
        'rules.minmarketcap',
        'rules.maxmarketcap',
        'rules.maxholdowner',
        'rules.holdertop',
        'rules.minholders',
        'rules.maxholders',
        'rules.checkholders',
        'rules.liquiditypool'
    ];

    readonlyFields.forEach(field => 
    {
        const selector = `[name="${field}"]`;
        if(filteroff === "True") 
        {
            $(selector).attr("readonly", true).addClass("readonlyfield").css("pointer-events", "none");
        } 
        else 
        {
            $(selector).removeAttr("readonly").removeClass("readonlyfield").css("pointer-events", "");
        }
    });
}

$(document).ready(function() 
{
    $('[name="filename"]').on('input keyup change', function() 
    {
        $('[name="main.name"]').val($(this).val());
    });

    toggleBotFields();
    toggleConditionalFields();

    $('[name="main.enabled"]').on('change', toggleBotFields);
    $('[name="filters.listener"], [name="trade.fastmode"], [name="trade.trailingstop"], [name="filters.filteroff"]').on('change', toggleConditionalFields);
});