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
    const botstatus = $('[name="main.status"]').val();
    if(botstatus === "True") 
    {
        $('.bot-fields').show();
    } 
    else 
    {
        $('.bot-fields').hide();
    }
}

function toggleBotSwitch(filename, botstatus) 
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
            status: botstatus
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

function toogleChangeFields() 
{
    const botstatus = $('[name="main.status"]').val();
    const sandbox = $('[name="main.sandbox"]').val();
    const fastmode = $('[name="trade.fastmode"]').val();
    const holderscheck = $('[name="rules.holderscheck"]').val();
    const trailprofit = $('[name="trade.trailprofit"]').val();

    if(botstatus === "True" && sandbox === "True") 
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

    if(holderscheck === "True") 
    {
        $('[name="rules.holdersbalance"]').closest('.mb-3').show();
    } 
    else 
    {
        $('[name="rules.holdersbalance"]').closest('.mb-3').hide();
    }

    if(trailprofit === "True") 
    {
        $('[name="trade.trailone"]').closest('.mb-3').show();
        $('[name="trade.trailtwo"]').closest('.mb-3').show();
        $('[name="trade.trailthree"]').closest('.mb-3').show();
        $('[name="trade.trailfour"]').closest('.mb-3').show();
        $('[name="trade.trailfive"]').closest('.mb-3').show();
    } 
    else 
    {
        $('[name="trade.trailone"]').closest('.mb-3').hide();
        $('[name="trade.trailtwo"]').closest('.mb-3').hide();
        $('[name="trade.trailthree"]').closest('.mb-3').hide();
        $('[name="trade.trailfour"]').closest('.mb-3').hide();
        $('[name="trade.trailfive"]').closest('.mb-3').hide();
    }
}

$(document).ready(function() 
{
    $('[name="filename"]').on('input keyup change', function() 
    {
        $('[name="main.name"]').val($(this).val());
    });

    toggleBotFields();
    toogleChangeFields();

    $('[name="main.status"]').on('change', function()
    {
        toggleBotFields();
        toogleChangeFields();
    });

    $('[name="main.sandbox"], [name="filters.listener"], [name="trade.fastmode"], [name="trade.trailprofit"], [name="rules.holderscheck"]').on('change', toogleChangeFields);
});
