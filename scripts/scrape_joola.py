"""
Scraper para Joola Brazil - Coleção de Pickleball
Extrai produtos de pickleball da loja oficial Joola.
"""
import asyncio
import csv
from pathlib import Path
from playwright.async_api import async_playwright
import re

# Paths
OUTPUT_CSV = Path(__file__).parent.parent / "data" / "raw" / "joola_brazil.csv"


def clean_price(price_text: str) -> float:
    """Extrair valor numérico do preço em BRL"""
    match = re.search(r'R\$?\s?([\d.,]+)', price_text)
    if match:
        price_str = match.group(1).replace('.', '').replace(',', '.')
        return float(price_str)
    return 0.0


async def scrape_joola_page(page, page_num: int) -> list[dict]:
    """Scrape uma página de produtos"""
    url = f"https://www.joola.com.br/collections/pickleball?page={page_num}"
    print(f"  📄 Acessando página {page_num}...")
    
    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)
    
    # Extrair produtos
    products = []
    product_cards = await page.query_selector_all('.product-item')
    
    print(f"  🔍 Encontrados {len(product_cards)} produtos na página {page_num}")
    
    for card in product_cards:
        try:
            # Nome do produto
            title_elem = await card.query_selector('.product-item-meta__title')
            if not title_elem:
                continue
            
            product_name = await title_elem.inner_text()
            product_url = await title_elem.get_attribute('href')
            if product_url and not product_url.startswith('http'):
                product_url = f"https://www.joola.com.br{product_url}"
            
            # Preço (promocional ou normal)
            price_elem = await card.query_selector('.price--highlight, .price')
            if price_elem:
                price_text = await price_elem.inner_text()
                price_brl = clean_price(price_text)
            else:
                price_brl = 0.0
            
            # Imagem
            img_elem = await card.query_selector('.product-item__primary-image')
            image_url = None
            if img_elem:
                # Tentar srcset primeiro (melhor qualidade)
                srcset = await img_elem.get_attribute('srcset')
                if srcset:
                    # Pegar a URL de maior resolução do srcset
                    urls = [part.strip().split()[0] for part in srcset.split(',')]
                    image_url = urls[-1] if urls else None
                
                # Fallback para src
                if not image_url:
                    image_url = await img_elem.get_attribute('src')
                
                # Adicionar protocolo se necessário
                if image_url and image_url.startswith('//'):
                    image_url = f"https:{image_url}"
            
            # Extrair marca e modelo do nome
            # Formato comum: "JOOLA Perseus CFS 16mm"
            # parts = product_name.split()  # Not used
            brand_name = "Joola"  # Loja oficial Joola
            model_name = product_name.replace("JOOLA", "").strip()
            
            products.append({
                'brand_name': brand_name,
                'model_name': model_name,
                'price_brl': price_brl,
                'product_url': product_url,
                'store_name': 'Joola Brazil',
                'image_url': image_url
            })
            
        except Exception:
            print("    ⚠️  Erro ao processar produto")
            continue
    
    return products


async def scrape_joola_store():
    """Scrape principal da loja Joola"""
    print("🏓 SliceInsights - Scraper Joola Brazil")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        all_products = []
        page_num = 1
        
        # Scrape todas as páginas
        while True:
            products = await scrape_joola_page(page, page_num)
            
            if not products:
                print(f"  ✅ Fim da paginação na página {page_num}")
                break
            
            all_products.extend(products)
            
            # Verificar se há próxima página
            next_link = await page.query_selector('a[rel="next"]')
            if not next_link:
                print(f"  ✅ Última página alcançada ({page_num})")
                break
            
            page_num += 1
        
        await browser.close()
    
    # Filtrar apenas raquetes (ignorar acessórios, roupas, etc.)
    paddle_keywords = ['mm', 'paddle', 'raw', 'cfs', 'perseus', 'vision', 'hyperion', 'ben johns', 'tyson mcguffin']
    
    paddles = []
    for product in all_products:
        model_lower = product['model_name'].lower()
        # Incluir se contém palavras-chave de raquete
        if any(keyword in model_lower for keyword in paddle_keywords):
            paddles.append(product)
    
    print("\n" + "=" * 60)
    print(f"📦 Total de produtos scraped: {len(all_products)}")
    print(f"🎾 Raquetes identificadas: {len(paddles)}")
    print("=" * 60)
    
    # Salvar CSV
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        if paddles:
            writer = csv.DictWriter(f, fieldnames=paddles[0].keys())
            writer.writeheader()
            writer.writerows(paddles)
    
    print(f"\n✅ Dados salvos em: {OUTPUT_CSV}")
    print(f"🎾 {len(paddles)} raquetes exportadas")
    
    # Mostrar exemplos
    if paddles:
        print("\n📋 Exemplos de raquetes encontradas:")
        for paddle in paddles[:5]:
            print(f"  • {paddle['brand_name']} {paddle['model_name']} - R$ {paddle['price_brl']:.2f}")


if __name__ == "__main__":
    asyncio.run(scrape_joola_store())
