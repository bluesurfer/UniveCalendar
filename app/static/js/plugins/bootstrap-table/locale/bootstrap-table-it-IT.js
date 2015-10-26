/**
 * Bootstrap Table Italian translation
 * Author: Davide Renzi<davide.renzi@gmail.com>
 */
(function ($) {
    'use strict';

    $.fn.bootstrapTable.locales['it-IT'] = {
        formatLoadingMessage: function () {
            return 'Caricamento in corso...';
        },
        formatRecordsPerPage: function (pageNumber) {
            return pageNumber + ' righe per pagina';
        },
        formatShowingRows: function (pageFrom, pageTo, totalRows) {
            return 'Righe da ' + pageFrom + ' a ' + pageTo + ' (' + totalRows + ' totali)';
        },
        formatSearch: function () {
            return 'Cerca';
        },
        formatNoMatches: function () {
            return 'Nessun record trovato';
        },
        formatRefresh: function () {
            return 'Rinfrescare';
        },
        formatToggle: function () {
            return 'Alternare';
        },
        formatColumns: function () {
            return 'Colonne';
        }
    };

    $.extend($.fn.bootstrapTable.defaults, $.fn.bootstrapTable.locales['it-IT']);

})(jQuery);
