import pandas as pd
import re

# Ler os CSVs
brazil = pd.read_csv('/app/data/raw/brazil_pickleball_store.csv')
international = pd.read_csv('/app/data/raw/paddle_stats_dump.csv')

print(f"📊 Total raquetes Brasil: {len(brazil)}")
print(f"📊 Total raquetes Internacional: {len(international)}")
print()

# Normalizar nomes para comparação
def normalize(text):
    if pd.isna(text):
        return ""
    text = str(text).lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text

# Criar chaves de comparação (marca + modelo)
brazil['brand_key'] = brazil['brand_name'].apply(normalize)
brazil['model_key'] = brazil['model_name'].apply(normalize)
brazil['full_key'] = brazil['brand_key'] + ' ' + brazil['model_key']

international['brand_key'] = international['Col_0'].apply(normalize)
international['model_key'] = international['Col_1'].apply(normalize)
international['full_key'] = international['brand_key'] + ' ' + international['model_key']

# Encontrar matches
matches = []
no_matches = []

for idx, row in brazil.iterrows():
    b_brand = row['brand_key']
    b_model = row['model_key']
    found = False
    
    for _, int_row in international.iterrows():
        i_brand = int_row['brand_key']
        i_model = int_row['model_key']
        
        # Match se marca é igual E modelo tem sobreposição significativa
        if b_brand == i_brand:
            # Verificar sobreposição de palavras no modelo
            b_words = set(b_model.split())
            i_words = set(i_model.split())
            common = b_words.intersection(i_words)
            
            # Se pelo menos 2 palavras em comum OU 60% de sobreposição
            if len(common) >= 2 or (len(common) / max(len(b_words), len(i_words)) >= 0.6):
                matches.append({
                    'brand': row['brand_name'],
                    'brazil_model': row['model_name'],
                    'int_model': int_row['Col_1'],
                    'price_brl': row['price_brl']
                })
                found = True
                break
    
    if not found:
        no_matches.append({
            'brand': row['brand_name'],
            'model': row['model_name'],
            'price': row['price_brl']
        })

print(f"🎯 Matches encontrados: {len(matches)}")
print(f"📈 Percentual: {len(matches)/len(brazil)*100:.1f}%")
print()

if matches:
    print("Raquetes com match no dataset internacional:")
    for i, m in enumerate(matches[:15], 1):
        print(f"  {i}. {m['brand']} - {m['brazil_model']}")

print("\n---\n")
print(f"❌ {len(no_matches)} raquetes EXCLUSIVAS do mercado brasileiro:")
for i, nm in enumerate(no_matches[:10], 1):
    print(f"  {i}. {nm['brand']} - {nm['model']} (R$ {nm['price']:.2f})")

if len(no_matches) > 10:
    print(f"  ... e mais {len(no_matches) - 10} raquetes")
