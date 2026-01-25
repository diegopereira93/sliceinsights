"""
Scraper para Mercado Livre Brasil
Busca "raquete pickleball" e extrai produtos
"""
import asyncio
import pandas as pd
from playwright.async_api import async_playwright
import re
from pathlib import Path

SEARCH_QUERY = "raquete pickleball"
BASE_URL = "https://lista.mercadolivre.com.br/"
OUTPUT_FILE = "data/raw/mercado_livre.csv"

async def scrape_mercado_livre():
    """Scrape pickleball paddles from Mercado Livre"""
    async with async_playwright() as p:
        print("🚀 Iniciando scraper do Mercado Livre...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        # Construir URL de busca
        search_url = f"{BASE_URL}{SEARCH_QUERY.replace(' ', '-')}"
        print(f"📡 Buscando por '{SEARCH_QUERY}' no Mercado Livre...")
        
        await page.goto(search_url, wait_until="networkidle")
        
        # Aguardar resultados
        try:
            await page.wait_for_selector('.ui-search-layout__item', timeout=10000)
        except:
            print("⚠️  Nenhum resultado encontrado")
            await browser.close()
            return []
        
        products = []
        
        print("🔍 Extraindo produtos...")
        # Buscar todos os cards de produtos
        product_elements = await page.query_selector_all('.ui-search-layout__item')
        
        for card in product_elements:
            try:
                # Título do produto
                title_element = await card.query_selector('.ui-search-item__title')
                if not title_element:
                    continue
                full_title = await title_element.inner_text()
                
                # URL do produto
                link_element = await card.query_selector('a.ui-search-link')
                product_url = await link_element.get_attribute('href') if link_element else ""
                
                # Preço
                price_element = await card.query_selector('.andes-money-amount__fraction')
                if price_element:
                    price_text = await price_element.inner_text()
                    # Limpar preço: "1.889" -> 1889.00
                    price_brl = float(price_text.replace('.', '').replace(',', '.'))
                else:
                    price_brl = 0.0
                
                # Imagem
                img_element = await card.query_selector('img')
                image_url = None
                if img_element:
                    image_url = await img_element.get_attribute('src')
                    if not image_url:
                        image_url = await img_element.get_attribute('data-src')
                
                # Inferir marca e modelo
                brand_name, model_name = parse_product_title(full_title)
                
                if price_brl > 0:  # Só adicionar se tiver preço válido
                    products.append({
                        'brand_name': brand_name,
                        'model_name': model_name,
                        'price_brl': price_brl,
                        'product_url': product_url,
                        'image_url': image_url or "",
                        'store_name': 'Mercado Livre'
                    })
                    
                    print(f"  ✅ {brand_name} - {model_name} - R$ {price_brl:.2f}")
                
            except Exception as e:
                print(f"  ⚠️  Erro ao processar produto: {e}")
                continue
        
        await browser.close()
        
        # Salvar em CSV
        if products:
            df = pd.DataFrame(products)
            # Criar diretório se não existir
            Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(OUTPUT_FILE, index=False)
            print(f"\n✅ {len(products)} produtos salvos em {OUTPUT_FILE}")
        else:
            print("\n⚠️  Nenhum produto encontrado!")
        
        return products


def parse_product_title(title: str) -> tuple[str, str]:
    """
    Parse product title to extract brand and model
    Ex: "Raquete Pickleball Selkirk Invikta 16mm Carbono"
    -> brand: "Selkirk", model: "Invikta 16mm Carbono"
    """
    # Remover palavras comuns
    title_clean = title
    for word in ['Raquete', 'Pickleball', 'Paddle', 'Kit', 'Com']:
        title_clean = re.sub(rf'\b{word}\b', '', title_clean, flags=re.IGNORECASE)
    title_clean = title_clean.strip()
    
    # Marcas conhecidas
    known_brands = [
        'Selkirk', 'SLK', 'CRBN', 'Joola', 'Paddletek', 'Engage', 
        'Franklin', 'Diadem', 'Gamma', 'Gearbox', 'Head', 'Adidas',
        'Electrum', 'Vatic', 'Vulcan', '11six24', '3rdshot', 'Onix',
        'Wilson', 'Pro Kennex', 'Yonex'
    ]
    
    brand_name = "Unknown"
    model_name = title_clean
    
    # Procurar marca no título
    for brand in known_brands:
        if brand.lower() in title.lower():
            brand_name = brand
            # Remover marca do modelo
            model_name = re.sub(rf'\b{brand}\b', '', title_clean, flags=re.IGNORECASE).strip()
            break
    
    # Se não encontrou marca conhecida, usar primeira palavra
    if brand_name == "Unknown":
        parts = title_clean.split()
        if parts:
            brand_name = parts[0]
            model_name = ' '.join(parts[1:]) if len(parts) > 1 else title_clean
    
    # Limpar espaços extras
    model_name = ' '.join(model_name.split())
    
    return brand_name, model_name


if __name__ == "__main__":
    asyncio.run(scrape_mercado_livre())
