
/* =========================================================
   KisanVision360+
   RESPONSIVE UI HELPERS

   IMPORTANT:
   Sidebar open/close JavaScript is handled in base.html.
   DO NOT add sidebar click listener here.
========================================================= */

(function () {

    "use strict";


    function ready(fn) {

        if (
            document.readyState === "loading"
        ) {

            document.addEventListener(
                "DOMContentLoaded",
                fn
            );

        } else {

            fn();

        }

    }


    ready(function () {


        /* =================================================
           RESPONSIVE TABLES
        ================================================== */

        document
            .querySelectorAll("table")
            .forEach(function (table) {

                if (
                    table.closest(
                        ".responsive-table, .table-responsive"
                    )
                ) {

                    return;

                }


                const parent =
                    table.parentElement;


                if (
                    parent &&
                    (
                        table.scrollWidth >
                        parent.clientWidth
                        ||
                        table.offsetWidth >
                        parent.clientWidth
                    )
                ) {

                    const wrapper =
                        document.createElement(
                            "div"
                        );


                    wrapper.className =
                        "table-responsive";


                    table.parentNode.insertBefore(
                        wrapper,
                        table
                    );


                    wrapper.appendChild(
                        table
                    );

                }

            });


        /* =================================================
           SAFE IMAGES
        ================================================== */

        document
            .querySelectorAll("img")
            .forEach(function (img) {


                if (!img.loading) {

                    img.loading = "lazy";

                }


                img.addEventListener(
                    "error",
                    function () {

                        this.classList.add(
                            "image-load-error"
                        );

                    }
                );

            });


        /* =================================================
           RESPONSIVE TABLE CSS
        ================================================== */

        if (
            !document.getElementById(
                "kvResponsiveTableStyle"
            )
        ) {

            const style =
                document.createElement("style");


            style.id =
                "kvResponsiveTableStyle";


            style.textContent = `

                .table-responsive {
                    width: 100%;
                    overflow-x: auto;
                    -webkit-overflow-scrolling: touch;
                }

                .table-responsive table {
                    min-width: 600px;
                }

                .image-load-error {
                    opacity: .5;
                }

                @media (max-width: 600px) {

                    .table-responsive table {
                        min-width: 500px;
                    }

                }

            `;


            document.head.appendChild(
                style
            );

        }


        console.log(
            "KisanVision360+: responsive.js loaded."
        );


    });


})();

