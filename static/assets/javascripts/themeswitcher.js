(function() 
{
    ((localStorage.getItem('theme') == 'auto' && window.matchMedia('(prefers-color-scheme: light)').matches) || localStorage.getItem('theme') == 'light') && document.documentElement.setAttribute('data-color-theme', 'light');
    localStorage.getItem('direction') == 'rtl' && document.getElementById("stylesheet").setAttribute('href', 'assets/stylesheets/rtl/all.min.css');
    localStorage.getItem('direction') == 'rtl' && document.documentElement.setAttribute('dir', 'rtl');
})();

const themeSwitcher = function() 
{
    const layoutTheme = function() 
    {
        var primaryTheme = 'dark';
        var secondaryTheme = 'light';
        var storageKey = 'theme';
        var colorscheme = document.getElementsByName('main-theme');
        var mql = window.matchMedia('(prefers-color-scheme: ' + primaryTheme + ')');

        function indicateTheme(mode) 
        {
            for(var i = colorscheme.length; i--;) 
            {
                if(colorscheme[i].value == mode) 
                {
                    colorscheme[i].checked = true;
                    colorscheme[i].closest('.list-group-item').classList.add('bg-primary', 'bg-opacity-10', 'border-primary');
                }
                else 
                {
                    colorscheme[i].closest('.list-group-item').classList.remove('bg-primary', 'bg-opacity-10', 'border-primary');
                }
            }
        };

        function applyTheme(mode) 
        {
            var st = document.documentElement;
            if(mode == primaryTheme) 
            {
                st.setAttribute('data-color-theme', 'dark');
            }
            else if(mode == secondaryTheme) 
            {
                st.setAttribute('data-color-theme', 'light');
            }
            else 
            {
                if(!mql.matches) 
                {
                    st.setAttribute('data-color-theme', 'light');
                }
                else 
                {
                    st.setAttribute('data-color-theme', 'dark');
                }
            }
        };

        function setTheme(e) 
        {
            var mode = e.target.value;
            document.documentElement.classList.add('no-transitions');
            if((mode == primaryTheme)) 
            {
                localStorage.removeItem(storageKey);
            }
            else 
            {
                localStorage.setItem(storageKey, mode);
            }
            
            autoTheme(mql);
        };

        function autoTheme(e) 
        {
            var current = localStorage.getItem(storageKey);
            var mode = primaryTheme;
            var indicate = primaryTheme;
            if(current != null) 
            {
                indicate = mode = current;
            }
            else if(e != null && e.matches) 
            {
                mode = primaryTheme;
            }
            applyTheme(mode);
            indicateTheme(indicate);
            setTimeout(function() 
            {
                document.documentElement.classList.remove('no-transitions');
            }, 100);
        };

        autoTheme(mql);
        mql.addListener(autoTheme);
        for(var i = colorscheme.length; i--;) 
        {
            colorscheme[i].onchange = setTheme;
        }
    };

    const layoutDirection = function() 
    {
        var dirSwitch = document.querySelector('[name="layout-direction"]');
        if(dirSwitch) 
        {
            var dirSwitchSelected = localStorage.getItem("direction") !== null && localStorage.getItem("direction") === "rtl";
            dirSwitch.checked = dirSwitchSelected;
            function resetDir() 
            {
                if(dirSwitch.checked) 
                {
                    document.getElementById("stylesheet").setAttribute('href', '/static/assets/stylesheets/rtl/default.min.css');
                    document.documentElement.setAttribute("dir", "rtl");
                    localStorage.setItem("direction", "rtl");
                } 
                else 
                {
                    document.getElementById("stylesheet").setAttribute('href', '/static/assets/stylesheets/ltr/default.min.css');
                    document.documentElement.setAttribute("dir", "ltr");
                    localStorage.removeItem("direction");
                }
            }

            dirSwitch.addEventListener("change", function() 
            {
                resetDir();
            });
        }
    };

    return {init: function() { layoutTheme(); layoutDirection(); }}
}();

document.addEventListener('DOMContentLoaded', function()
{
    themeSwitcher.init();
});