document.addEventListener('DOMContentLoaded', function() {
    let dark = document.querySelector('#darkSwitch');
    let body = document.querySelector('body');
    let nav = document.querySelector('.navbar');
    let dropdown = document.querySelector('.dropdown-menu');
    let modal = document.querySelectorAll('.modal-content');
    let cards = document.querySelectorAll('.card');
    let accordionbutton = document.querySelectorAll('.accordion-button');
    let accordionitem = document.querySelectorAll('.accordion-item');
    let table = document.querySelectorAll('.table');
    let materials = document.querySelectorAll('#material-buttons');
    let preference = localStorage.getItem('theme');

    function modeToggle() {
        body.classList.toggle("dark-body");
        nav.classList.toggle("bg-light");
        nav.classList.toggle("navbar-light");
        nav.classList.toggle("bg-dark");
        nav.classList.toggle("navbar-dark");
        if (dropdown) {
            dropdown.classList.toggle("bg-light");
            dropdown.classList.toggle("bg-dark");
        }
        for (let i = 0; i < cards.length; i++) {
            cards[i].classList.toggle("dark-cards");
        }
        for (let i = 0; i < accordionbutton.length; i++) {
            accordionbutton[i].classList.toggle("dark-accordion");
        }
        for (let i = 0; i < accordionitem.length; i++) {
            accordionitem[i].classList.toggle("dark-cards");
        }
        for (let i = 0; i < table.length; i++) {
            table[i].classList.toggle("table-dark");
        }
        for (let i = 0; i < materials.length; i++) {
            materials[i].classList.remove("btn-light");
            materials[i].classList.add("btn-dark");
        }
        for (let i = 0; i < modal.length; i++) {
            modal[i].classList.toggle("dark-cards");
        }
    }

    if (!preference) {
        localStorage.setItem('theme', 'light');
        preference = localStorage.getItem('theme');
    }
    if (preference === 'dark') {
        modeToggle()
        if (dark) {
            dark.setAttributeNode(document.createAttribute("checked"));
        }
    }

    if (dark) {
        dark.addEventListener('click', function() {
            if (preference === 'light') {
                localStorage.setItem('theme', 'dark');
            } else {
                localStorage.setItem('theme', 'light');
            }
            modeToggle()
        });
    }
});