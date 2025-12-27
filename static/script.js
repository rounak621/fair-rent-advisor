const app = {
    cities: JSON.parse(document.getElementById('cities-data').textContent),
    map: JSON.parse(document.getElementById('map-data').textContent),
    mlData: null,
    history: [],

    init() {
        lucide.createIcons();
        this.fillCities();
        this.bind();
    },

    fillCities() {
        const cS = document.getElementById('city');
        this.cities.forEach(c => cS.add(new Option(c, c)));
        this.fillLocs();
    },

    fillLocs() {
        const c = document.getElementById('city').value;
        const lS = document.getElementById('locality');
        lS.innerHTML = "";
        (this.map[c] || []).forEach(l => lS.add(new Option(l, l)));
    },

    async predict() {
        const btn = document.getElementById('predict-btn');
        btn.innerText = "Analyzing...";
        const res = await fetch('/predict', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                city: document.getElementById('city').value,
                locality: document.getElementById('locality').value,
                bhk: document.getElementById('bhk').value,
                area: document.getElementById('area').value || 1000,
                furnishing: "Semi-Furnished"
            })
        });
        this.mlData = await res.json();
        document.getElementById('ml-result').classList.remove('hidden');
        document.getElementById('rent-val').innerText = `₹${this.mlData.fair_rent_low.toLocaleString()}`;
        btn.innerText = "Analyze Rent";
    },

    openChat() {
        // Layout Transformation
        document.getElementById('form-container').classList.replace('lg:col-span-12', 'lg:col-span-5');
        const chat = document.getElementById('chat-container');
        chat.classList.remove('hidden');
        
        // FOCUS FIX: Force the browser to recognize the input
        setTimeout(() => {
            const input = document.getElementById('user-input');
            input.focus();
            input.select();
        }, 100);

        document.getElementById('unlock-chat').classList.add('hidden');
    },

    async chat() {
        const input = document.getElementById('user-input');
        const val = input.value.trim();
        if(!val) return;

        this.history.push({role: 'user', text: val});
        this.render();
        input.value = "";
        
        const box = document.getElementById('chat-box');
        box.insertAdjacentHTML('beforeend', `<div id="ai-loading" class="text-xs font-bold text-blue-500 animate-pulse">Strategist is thinking...</div>`);
        box.scrollTop = box.scrollHeight;

        const res = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                user_question: val,
                ml_data: this.mlData,
                chat_history: this.history.map(h => h.text).join("\n")
            })
        });
        const data = await res.json();
        document.getElementById('ai-loading').remove();
        this.history.push({role: 'ai', text: data.llm_response});
        this.render();
        input.focus();
    },

    render() {
        const box = document.getElementById('chat-box');
        box.innerHTML = this.history.map(h => `
            <div class="flex ${h.role==='user'?'justify-end':'justify-start'}">
                <div class="max-w-[85%] p-4 rounded-2xl ${h.role==='user'?'bg-blue-600 text-white shadow-lg':'bg-white border border-slate-100 prose shadow-sm'}">
                    ${h.role==='user' ? h.text : marked.parse(h.text)}
                </div>
            </div>
        `).join('');
        box.scrollTop = box.scrollHeight;
    },

    bind() {
        document.getElementById('city').onchange = () => this.fillLocs();
        document.getElementById('predict-btn').onclick = () => this.predict();
        document.getElementById('unlock-chat').onclick = () => this.openChat();
        document.getElementById('send-btn').onclick = () => this.chat();
        document.getElementById('user-input').onkeydown = (e) => {
            if(e.key === 'Enter') {
                e.preventDefault(); // Important: Stops form submission
                this.chat();
            }
        };
    }
};

document.addEventListener('DOMContentLoaded', () => app.init());