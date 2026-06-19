const data = [ { "country_code": "6", "full_name": "V Aaditya", "id": "1269873" } ];
const isBatter = true;
const html = data.map(p => {
    const safeName = (p.full_name || '').replace(/'/g, "\\'");
    return `
    <div class="search-item" onclick="selectPlayer('${p.id}', '${safeName}', ${isBatter})">
        <div style="font-weight: 600;">${p.full_name}</div>
    </div>
    `;
}).join('');
console.log(html);
