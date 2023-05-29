class Toast {
    constructor(params) {
        this._title = params['title'] === false ? false : params['title'] || '';
        this._text = params['text'] || '';
        this._theme = params['theme'] || 'default';
        this._autoHide = params['autoHide'] && true;
        this._addContainer = params['addContainer'] && true;
        this._interval = +params['interval'] || 5000;
        this._create();
        this._el.addEventListener('click', (e) => {
            if (e.target.classList.contains('toast__close')) {
                this._hide();
            }
        });
        this._show();
    }
    _show() {
        this._el.dispatchEvent(new Event('show.toast', {bubbles: true}));
        this._el.classList.add('toast_showing');
        this._el.classList.add('toast_show');
        window.setTimeout(() => {
            this._el.classList.remove('toast_showing');
        });
        if (this._autoHide) {
            setTimeout(() => {
                this._hide();
            }, this._interval);
        }
    }
    _hide() {
        this._el.classList.add('toast_showing');
        this._el.addEventListener('transitionend', () => {
            this._el.remove();
        }, {once : true});
        this._el.dispatchEvent(new Event('hide.toast', {bubbles: true}))
    }
    _create() {
        const el = document.createElement('div');
        el.classList.add('toast');
        el.classList.add(`toast_${this._theme}`);
        let html = `{header}<div class="toast__body"></div><button class="toast__close" type="button"></button>`;
        const htmlHeader = this._title === false ? '' : '<div class="toast__header"></div>';
        html = html.replace('{header}', htmlHeader);
        el.innerHTML = html;
        if (this._title) {
            el.querySelector('.toast__header').innerHTML = this._title;
        } else {
            el.classList.add('toast_message');
        }
        el.querySelector('.toast__body').innerHTML = this._text;
        this._el = el;
        if (!document.querySelector('.toast-container')) {
            const container = document.createElement('div');
            container.classList.add('toast-container');
            document.body.append(container);
        }
        if (this._addContainer) {
            document.querySelector('.toast-container').append(this._el);
        } else {
            document.querySelector('.toast-container').innerHTML = '';
            document.querySelector('.toast-container').append(this._el);
        }

    }
    static hide(el) {
        el.classList.add('toast_showing');
        el.addEventListener('transitionend', () => {
            el.remove();
        }, {once : true});
        el.dispatchEvent(new Event('hide.toast', {bubbles: true}))
    }
}