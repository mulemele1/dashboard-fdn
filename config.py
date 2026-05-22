# config.py
# Metas de Chefes de Agregado por distrito (PREVISTOS)
DISTRICT_TARGETS = {
    "Distrito de Mecubúri": 150,
    "Distrito de Ribáuè": 120,
    "Distrito de Lalaua": 80,
}

# Lista de distritos
DISTRICTS = list(DISTRICT_TARGETS.keys())

# Nomes dos inquiridores (para validação)
ENUMERATORS = [
    "Abel Araújo", "Anapaula Joaquim", "Anísio Rafael",
    "Assane Abudo", "Carla Bonifácio", "Felismino Bartolomeu",
    "Flora Augusto", "Juvência Ernesto", "Paulina Jemusse", "Sualehe Abacar"
]

# Mapeamento de colunas (baseado nos CSVs)
COLUMN_MAPPING = {
    # CAF Parte 1 (666877)
    "caf1": {
        "inquirer": "Nome do Inquirido?",
        "district": "Em que Distrito está a realizar o levantamento??",
        "admin_post": "Em que Posto Administrativo está a realizar o levantamento?",
        "village": "Indique o Povoado/comunidade em que o agregado familiar está localizado.",
        "respondent_name": "Nome do entrevistado?",
        "is_head": "O entrevistado é o chefe do agregado familiar?",
        "relationship": "Se não, Que relação tem com o Chefe do Agregado Familiar?",
        "head_name": "Qual é o nome do Chefe do Agregado Familiar?",
        "participated_mapping": "O Chefe do Agregado familiar Participou no processo de Mapeamento feito pela Fórum Terra?",
        "gender": "Sexo do chefe de agregado",
        "age": "Qual é a idade do chefe de agregado?",
        "submission_date": "Data de submissão",
        "gps": "Por favor clique no icone para captar a localização"
    },
    # CAF Parte 2 (163198)
    "caf2": {
        "inquirer": "Nome do Inquirido?",
        "submission_date": "Data de submissão",
        "livestock": "O Agregado Familiar cria animais?",
        "charcoal": "O Agregado familiar produz carvão vegetal?",
        "fishing": "O Agregado Familiar pratica a actividade pesqueira?",
        "income_sources": "Principais fontes de rendimento",
        "house_material": "A sua casa é construída com",
        "roof_material": "A casa está coberta de",
        "water_source": "Qual é a fonte de água que usa para beber?",
        "sanitation": "Que tipo de sanitário usam os membros do seu agregado familiar?",
        "meals_per_day": "Normalmente, quantas refeições o agregado familiar come por dia?",
        "food_security": "Nos últimos 30 dias, passou por períodos de escassez/falta de alimentos?"
    },
    # MAF (757779)
    "maf": {
        "inquirer": "Nome do Chefe do Agregado familiar",
        "submission_date": "Date submitted",
        "member_name": "Nome completo (nome da pessoa pertence ao agregado familiar):",
        "member_relation": "Assinale a relação do membro do agregado familiar com o chefe de família:",
        "member_gender": "Sexo.",
        "member_age": "Idade do membro do agregado familiar em anos (valor inteiro, mínimo 0):",
        "member_education": "Nível de escolaridade do/a membro do agregado familiar:",
        "member_occupation": "Qual é a principal a ocupação do membro do agregado familiar?",
        "member_income": "O membro recebe renda dessa actividade principal?"
    }
}