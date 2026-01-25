"""
Scraper para Brazil Pickleball Store
Extrai produtos de pickleball vendidos no Brasil
"""
import asyncio
import pandas as pd
from playwright.async_api import async_playwright
import re
from pathlib import Path

TARGET_URL = "https://www.brazilpickleballstore.com.br/raquete/"
OUTPUT_FILE = "data/raw/brazil_pickleball_store.csv"

async def scrape_brazil_store():
    """Scrape products from Brazil Pickleball Store"""
    async with async_playwright() as p:
        print("🚀 Iniciando scraper da Brazil Pickleball Store...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        print(f"📡 Navegando para {TARGET_URL}...")
        await page.goto(TARGET_URL, wait_until="networkidle")
        
        # Aguardar produtos carregarem
        await page.wait_for_selector('.js-item-product', timeout=30000)
        
        products = []
        
        print("🔍 Extraindo produtos...")
        # Buscar todos os cards de produtos
        product_elements = await page.query_selector_all('.js-item-product')
        
        for card in product_elements:
            try:
                # Extrair título completo do produto
                title_element = await card.query_selector('.js-item-name')
                full_title = await title_element.inner_text() if title_element else "Unknown"
                
                # Extrair link do produto
                link_element = await card.query_selector('a')
                product_url = await link_element.get_attribute('href') if link_element else ""
                
                # Extrair preço (procurar por elementos com R$)
                price_element = await card.query_selector('.js-price-display')
                if not price_element:
                    # Tentar seletor alternativo
                    price_element = await card.query_selector('[class*="price"]')
                
                if price_element:
                    price_text = await price_element.inner_text()
                    # Limpar preço: "R$ 1.889,00" -> 1889.00
                    price_match = re.search(r'R\$?\s*([\d.,]+)', price_text.replace('.', '').replace(',', '.'))
                    price_brl = float(price_match.group(1)) if price_match else 0.0
                else:
                    price_brl = 0.0
                
                # Extrair imagem (usando data-srcset do lazy loading)
                img_element = await card.query_selector('img.js-product-item-image-private, img.product-item-image-featured')
                image_url = None
                if img_element:
                    # Tentar data-srcset primeiro (contém URLs em alta resolução)
                    data_srcset = await img_element.get_attribute('data-srcset')
                    if data_srcset:
                        # data-srcset tem formato: "url1 size1, url2 size2, ..."
                        # Pegar a última URL (maior resolução)
                        urls = [part.strip().split()[0] for part in data_srcset.split(',')]
                        if urls:
                            image_url = urls[-1]  # Última URL = maior resolução
                    
                    # Fallback: tentar srcset
                    if not image_url:
                        srcset = await img_element.get_attribute('srcset')
                        if srcset:
                            urls = [part.strip().split()[0] for part in srcset.split(',')]
                            if urls:
                                image_url = urls[-1]
                    
                    # Adicionar https: se for protocol-relative
                    if image_url and image_url.startswith('//'):
                        image_url = f"https:{image_url}"
                    elif image_url and not image_url.startswith('http'):
                        image_url = f"https://www.brazilpickleballstore.com.br{image_url}"
                
                # Inferir marca e modelo do título
                brand_name, model_name = parse_product_title(full_title)
                
                if price_brl > 0:  # Só adicionar se tiver preço válido
                    products.append({
                        'brand_name': brand_name,
                        'model_name': model_name,
                        'price_brl': price_brl,
                        'product_url': product_url if product_url and product_url.startswith('http') else f"https://www.brazilpickleballstore.com.br{product_url}",
                        'image_url': image_url or "",
                        'store_name': 'Brazil Pickleball Store'
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
    Ex: "Raquete Selkirk Invikta Luxx Control InfiniGrit 19mm"
    -> brand: "Selkirk", model: "Invikta Luxx Control InfiniGrit 19mm"
    """
    # Remover prefixos comuns
    title = title.replace('Raquete', '').replace('Kit', '').strip()
    
    # Marcas conhecidas
    known_brands = [
        'Selkirk', 'SLK', 'CRBN', 'Joola', 'Paddletek', 'Engage', 
        'Franklin', 'Diadem', 'Gamma', 'Gearbox', 'Head', 'Adidas',
        'Electrum', 'Vatic', 'Vulcan', '11six24', '3rdshot', 'Onix'
    ]
    
    brand_name = "Unknown"
    model_name = title
    
    # Procurar marca no início do título
    for brand in known_brands:
        if title.lower().startswith(brand.lower()):
            brand_name = brand
            model_name = title[len(brand):].strip()
            break
    
    # Se não encontrou, tentar achar no meio
    if brand_name == "Unknown":
        for brand in known_brands:
            if brand.lower() in title.lower():
                brand_name = brand
                # Pegar tudo exceto a marca
                model_name = title.replace(brand, '').strip()
                break
    
    # Se ainda não encontrou, usar primeira palavra como marca
    if brand_name == "Unknown":
        parts = title.split()
        if parts:
            brand_name = parts[0]
            model_name = ' '.join(parts[1:]) if len(parts) > 1 else title
    
    return brand_name, model_name


if __name__ == "__main__":
    asyncio.run(scrape_brazil_store())
