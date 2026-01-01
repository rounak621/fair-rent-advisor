const app = {
    cities: JSON.parse(document.getElementById('cities-data').textContent),
    map: JSON.parse(document.getElementById('map-data').textContent),
    mlData: null,
    history: [],

    formatter: new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0,
    }),

    init() {
        lucide.createIcons();
        this.fillCities();
        this.bind();
    },

    fillCities() {
        const cS = document.getElementById('city');
        if (!cS) return;
        this.cities.forEach(c => cS.add(new Option(c, c)));
        this.fillLocs();
    },

    fillLocs() {
        const c = document.getElementById('city').value;
        const lS = document.getElementById('locality');
        if (!lS) return;
        lS.innerHTML = "";
        (this.map[c] || []).forEach(l => lS.add(new Option(l, l)));
    },

    async predict() {
        const btn = document.getElementById('predict-btn');
        const originalContent = btn.innerHTML;
        
        btn.disabled = true;
        btn.innerHTML = `<div class="animate-spin rounded-full h-5 w-5 border-2 border-white/30 border-t-white"></div>`;

        try {
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
            document.getElementById('results-placeholder').classList.add('hidden');
            const resultCard = document.getElementById('ml-result');
            resultCard.classList.remove('hidden');

            const avgRent = (this.mlData.fair_rent_low + this.mlData.fair_rent_high) / 2;
            document.getElementById('rent-val').innerText = this.formatter.format(avgRent);
            document.getElementById('rent-range').innerText = 
                `Confidence Range: ${this.formatter.format(this.mlData.fair_rent_low)} — ${this.formatter.format(this.mlData.fair_rent_high)}`;

        } catch (error) {
            console.error(error);
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalContent;
        }
    },

    openChat() {
        const chat = document.getElementById('chat-container');
        chat.classList.remove('hidden');
        chat.scrollIntoView({ behavior: 'smooth', block: 'start' });
        setTimeout(() => document.getElementById('user-input').focus(), 400);
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
        const loadingId = "ai-loading-" + Date.now();
        
        box.insertAdjacentHTML('beforeend', `
            <div id="${loadingId}" class="flex justify-start">
                <div class="ai-bubble p-5 rounded-2xl text-[10px] font-bold text-slate-400 shimmer">
                    STRATEGIST COMPILING RESPONSE...
                </div>
            </div>
        `);
        box.scrollTop = box.scrollHeight;

        try {
            const res = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    user_question: val,
                    ml_data: this.mlData,
                    chat_history: this.history.map(h => `${h.role}: ${h.text}`).join("\n")
                })
            });
            
            const data = await res.json();
            document.getElementById(loadingId).remove();
            this.history.push({role: 'ai', text: data.llm_response});
            this.render();
        } catch (e) {
            document.getElementById(loadingId).innerHTML = `<span class="text-red-400">Communication Link Severed.</span>`;
        }
    },

    render() {
        const box = document.getElementById('chat-box');
        box.innerHTML = this.history.map(h => `
            <div class="flex ${h.role === 'user' ? 'justify-end' : 'justify-start'}">
                <div class="max-w-[85%] p-5 rounded-2xl ${
                    h.role === 'user' 
                    ? 'user-bubble text-white shadow-lg shadow-indigo-500/20' 
                    : 'ai-bubble text-slate-200'
                }">
                    <div class="text-sm prose prose-invert prose-sm">
                        ${h.role === 'user' ? h.text : marked.parse(h.text)}
                    </div>
                </div>
            </div>
        `).join('');
        box.scrollTop = box.scrollHeight;
    },

    bind() {
        document.getElementById('city').addEventListener('change', () => this.fillLocs());
        document.getElementById('predict-btn').addEventListener('click', () => this.predict());
        document.getElementById('unlock-chat').addEventListener('click', () => this.openChat());
        document.getElementById('send-btn').addEventListener('click', () => this.chat());
        document.getElementById('user-input').addEventListener('keydown', (e) => {
            if(e.key === 'Enter') {
                e.preventDefault();
                this.chat();
            }
        });
    }
};

document.addEventListener('DOMContentLoaded', () => app.init());