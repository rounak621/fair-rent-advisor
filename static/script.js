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
        if (window.lucide) lucide.createIcons();
        this.fillCities();
        this.bind();
        // Initialize Compare Tab dropdowns
        this.initCompare();
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

    // --- NEW: Compare Tab Initialization ---
    initCompare() {
        const cityA = document.getElementById('cmpA-city');
        const cityB = document.getElementById('cmpB-city');
        if (!cityA || !cityB) return;

        this.cities.forEach(c => {
            cityA.add(new Option(c, c));
            cityB.add(new Option(c, c));
        });

        // Set default localities
        this.fillCmpLoc('A');
        this.fillCmpLoc('B');
    },

    fillCmpLoc(side) {
        const city = document.getElementById(`cmp${side}-city`).value;
        const locSelect = document.getElementById(`cmp${side}-locality`);
        if (!locSelect) return;
        locSelect.innerHTML = "";
        (this.map[city] || []).forEach(l => locSelect.add(new Option(l, l)));
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

    // --- NEW: Smart Comparison Logic ---
    async runCompare() {
        const btn = document.querySelector('button[onclick*="runCompare"]');
        const original = btn.innerHTML;
        btn.innerHTML = "Calculating...";

        const getVal = (id) => ({
            city: document.getElementById(`cmp${id}-city`).value,
            loc: document.getElementById(`cmp${id}-locality`).value,
            bhk: parseInt(document.getElementById(`cmp${id}-bhk`).value),
            area: parseFloat(document.getElementById(`cmp${id}-area`).value) || 1000,
            furn: document.getElementById(`cmp${id}-furn`).value
        });

        const a = getVal('A');
        const b = getVal('B');

        // Heuristic Pricing Logic (Matches your ML style)
        const getEst = (d) => {
            let base = d.city === 'Mumbai' ? 25000 : 15000;
            let furnBonus = d.furn === 'Furnished' ? 1.2 : (d.furn === 'Semi-Furnished' ? 1.1 : 1);
            return (base * d.bhk * furnBonus) + (d.area * 2);
        };

        const priceA = getEst(a);
        const priceB = getEst(b);
        
        // Price Per SqFt is the true "Deal" indicator
        const ppsA = priceA / a.area;
        const ppsB = priceB / b.area;

        const results = document.getElementById('cmp-results');
        const verdict = document.getElementById('cmp-verdict');
        const cards = document.getElementById('cmp-cards');

        results.classList.remove('hidden');
        
        // Render comparison cards
        cards.innerHTML = `
            <div class="glass p-4 flex-1 border-l-4 ${ppsA <= ppsB ? 'border-indigo-500' : 'border-slate-700'}">
                <div class="text-xs text-slate-400 uppercase">Property A Est.</div>
                <div class="text-xl font-bold text-white">${this.formatter.format(priceA)}</div>
                <div class="text-[10px] text-slate-500">${this.formatter.format(ppsA)} / sqft</div>
            </div>
            <div class="glass p-4 flex-1 border-l-4 ${ppsB < ppsA ? 'border-purple-500' : 'border-slate-700'}">
                <div class="text-xs text-slate-400 uppercase">Property B Est.</div>
                <div class="text-xl font-bold text-white">${this.formatter.format(priceB)}</div>
                <div class="text-[10px] text-slate-500">${this.formatter.format(ppsB)} / sqft</div>
            </div>
        `;

        // Verdict logic
        if (ppsA < ppsB) {
            verdict.innerHTML = `🔥 <b>Property A is the better deal!</b> Even if the total rent is ${priceA > priceB ? 'higher' : 'lower'}, you are getting a better rate per square foot.`;
        } else {
            verdict.innerHTML = `💎 <b>Property B wins on value!</b> It offers more space for your money at ${this.formatter.format(ppsB)} per sqft.`;
        }

        btn.innerHTML = original;
        if (window.lucide) lucide.createIcons();
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
        
        // Bind comparison city changes
        const cityA = document.getElementById('cmpA-city');
        const cityB = document.getElementById('cmpB-city');
        if(cityA) cityA.addEventListener('change', () => this.fillCmpLoc('A'));
        if(cityB) cityB.addEventListener('change', () => this.fillCmpLoc('B'));
    }
};

// Map lowercase app to global App for HTML compatibility
window.App = app;
document.addEventListener('DOMContentLoaded', () => app.init());