// Yandex.Metrika counter — вынесен из index.html в отдельный статический
// файл, чтобы Content-Security-Policy мог задавать script-src 'self' без
// 'unsafe-inline' (инлайн-скрипты в <head> иначе пришлось бы разрешать
// глобально). Содержимое не менялось, только место — см. Caddyfile.
//
// Номер счётчика продублирован в noscript-пикселе (index.html) и нужен
// роутеру для отправки просмотров при переходах внутри SPA
// (src/router/index.js), поэтому объявлен отдельной константой и выставлен
// в window — /metrika.js грузится обычным <script>, не модулем, и
// импортировать из него нечего.
var YM_COUNTER_ID = 112292853
window.YM_COUNTER_ID = YM_COUNTER_ID

;(function(m,e,t,r,i,k,a){
    m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
    m[i].l=1*new Date();
    for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
    k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
})(window, document,'script','https://mc.yandex.ru/metrika/tag.js?id=' + YM_COUNTER_ID, 'ym');

ym(YM_COUNTER_ID, 'init', {ssr:true, webvisor:true, clickmap:true, ecommerce:"dataLayer", referrer: document.referrer, url: location.href, accurateTrackBounce:true, trackLinks:true});
