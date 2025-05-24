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
    const enabled = $('[name="main.enabled"]').val();
    const sandbox = $('[name="main.sandbox"]').val();
    const filteroff = $('[name="filters.filteroff"]').val();
    const fastmode = $('[name="trade.fastmode"]').val();

    if(enabled === "True" && sandbox === "True") 
    {
        $('[name="main.initbalance"]').closest('.mb-3').show();
    } 
    else 
    {
        $('[name="main.initbalance"]').closest('.mb-3').hide();
    }

    if(fastmode === "True") 
    {
        $('[name="trade.fasttokens"]').closest('.mb-3').show();
    } 
    else 
    {
        $('[name="trade.fasttokens"]').closest('.mb-3').hide();
    }

    const readonlyFields = 
    [
        'filters.matchstring',
        'filters.matchaddress',
        'filters.noshorting',
        'timing.tokenmaxage',
        'rules.minmarketcap',
        'rules.maxmarketcap',
        'rules.minmarketvol',
        'rules.maxmarketvol',
        'rules.minholdowner',
        'rules.maxholdowner',
        'rules.topholders',
        'rules.minholders',
        'rules.maxholders',
        'rules.checkholders',
        'rules.minliquidity',
        'rules.maxliquidity'
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

    $('[name="main.enabled"]').on('change', function()
    {
        toggleBotFields();
        toggleConditionalFields();
    });

    $('[name="main.sandbox"], [name="filters.listener"], [name="trade.fastmode"], [name="trade.trailingstop"], [name="filters.filteroff"]').on('change', toggleConditionalFields);
});