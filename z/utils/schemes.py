
# ============================================================
# KISANVISION360+
# GOVERNMENT AGRICULTURAL SCHEMES DATABASE
# ============================================================
#
# File:
#     utils/schemes.py
#
# Purpose:
#     Central source of truth for Government Schemes.
#
# IMPORTANT:
#     This file does NOT use PostgreSQL/Supabase.
#     The Government Schemes module reads data directly from
#     this Python file.
#
# Total schemes:
#     55
#
# Each scheme contains:
#     name
#     department
#     purpose
#     eligibility
#     category
#     farmer_need
#     benefit_type
#     link
#     official
#     status
#
# ============================================================

from typing import List, Dict, Any, Optional


# ============================================================
# SCHEME DATABASE
# ============================================================

SCHEMES: List[Dict[str, Any]] = [

    # ========================================================
    # 1. PM-KISAN
    # ========================================================
    {
        "name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Provides income support to eligible farmer families.",
        "eligibility": "Eligible farmer families owning cultivable land, subject to government exclusion rules.",
        "category": "Financial Support",
        "farmer_need": "Financial assistance",
        "benefit_type": "Direct Benefit Transfer",
        "link": "https://pmkisan.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 2. PMFBY
    # ========================================================
    {
        "name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Provides crop insurance against notified crop losses and risks.",
        "eligibility": "Farmers growing notified crops in notified areas and seasons.",
        "category": "Crop Insurance",
        "farmer_need": "Crop loss protection",
        "benefit_type": "Crop Insurance",
        "link": "https://pmfby.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 3. KCC
    # ========================================================
    {
        "name": "Kisan Credit Card (KCC)",
        "department": "Ministry of Finance / Ministry of Agriculture and Farmers Welfare",
        "purpose": "Provides timely credit for crop cultivation and agricultural allied activities.",
        "eligibility": "Owner cultivators, tenant farmers, sharecroppers and eligible farmer groups.",
        "category": "Credit & Finance",
        "farmer_need": "Agricultural loan",
        "benefit_type": "Credit Facility",
        "link": "https://www.myscheme.gov.in/schemes/kcc",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 4. PMKSY
    # ========================================================
    {
        "name": "Pradhan Mantri Krishi Sinchayee Yojana (PMKSY)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Improves irrigation coverage and promotes efficient use of water.",
        "eligibility": "Eligible farmers and beneficiaries under applicable components.",
        "category": "Irrigation",
        "farmer_need": "Irrigation and water management",
        "benefit_type": "Irrigation Support",
        "link": "https://pmksy.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 5. SOIL HEALTH CARD
    # ========================================================
    {
        "name": "Soil Health Card Scheme",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Provides soil testing information and recommendations for balanced fertilizer use.",
        "eligibility": "Farmers whose agricultural soil is covered under soil testing programmes.",
        "category": "Soil & Fertilizer",
        "farmer_need": "Soil testing",
        "benefit_type": "Soil Health Recommendation",
        "link": "https://soilhealth.dac.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 6. e-NAM
    # ========================================================
    {
        "name": "National Agriculture Market (e-NAM)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Provides an electronic agricultural trading platform connecting agricultural markets.",
        "eligibility": "Farmers and other eligible market participants through participating markets.",
        "category": "Marketing",
        "farmer_need": "Better agricultural market access",
        "benefit_type": "Online Agricultural Market",
        "link": "https://www.enam.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 7. PM-KUSUM
    # ========================================================
    {
        "name": "PM-KUSUM",
        "department": "Ministry of New and Renewable Energy",
        "purpose": "Promotes solar energy applications for agriculture including solar pumps.",
        "eligibility": "Farmers and other eligible beneficiaries under state and component guidelines.",
        "category": "Solar & Energy",
        "farmer_need": "Solar irrigation",
        "benefit_type": "Solar Energy Support",
        "link": "https://pmkusum.mnre.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 8. AIF
    # ========================================================
    {
        "name": "Agriculture Infrastructure Fund (AIF)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Supports investment in post-harvest infrastructure and agricultural assets.",
        "eligibility": "Eligible farmers, FPOs, cooperatives, agri-entrepreneurs and other approved entities.",
        "category": "Infrastructure",
        "farmer_need": "Farm infrastructure",
        "benefit_type": "Infrastructure Financing",
        "link": "https://agriinfra.dac.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 9. NFSM
    # ========================================================
    {
        "name": "National Food Security Mission (NFSM)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Increases production and productivity of selected food crops.",
        "eligibility": "Farmers in areas covered by applicable state and programme interventions.",
        "category": "Crop Production",
        "farmer_need": "Higher crop production",
        "benefit_type": "Production Support",
        "link": "https://nfsm.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 10. PKVY
    # ========================================================
    {
        "name": "Paramparagat Krishi Vikas Yojana (PKVY)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Promotes cluster-based organic farming and sustainable agricultural practices.",
        "eligibility": "Eligible farmer groups and clusters under programme guidelines.",
        "category": "Organic Farming",
        "farmer_need": "Organic farming",
        "benefit_type": "Organic Farming Support",
        "link": "https://pgsindia-ncof.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 11. MIDH
    # ========================================================
    {
        "name": "Mission for Integrated Development of Horticulture (MIDH)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Promotes development of fruits, vegetables, flowers, spices and other horticultural crops.",
        "eligibility": "Eligible horticulture farmers and beneficiaries under state programmes.",
        "category": "Horticulture",
        "farmer_need": "Horticulture development",
        "benefit_type": "Horticulture Support",
        "link": "https://midh.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 12. NMSA
    # ========================================================
    {
        "name": "National Mission for Sustainable Agriculture (NMSA)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Promotes climate-resilient and sustainable agricultural practices.",
        "eligibility": "Eligible farmers and beneficiaries under applicable components.",
        "category": "Sustainable Farming",
        "farmer_need": "Sustainable agriculture",
        "benefit_type": "Sustainable Farming Support",
        "link": "https://nmsa.dac.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 13. SMAM
    # ========================================================
    {
        "name": "Sub-Mission on Agricultural Mechanization (SMAM)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Promotes access to modern agricultural machinery and farm mechanization.",
        "eligibility": "Eligible farmers and approved agricultural machinery beneficiaries.",
        "category": "Farm Machinery",
        "farmer_need": "Farm machinery",
        "benefit_type": "Machinery Assistance",
        "link": "https://agrimachinery.nic.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 14. RKVY
    # ========================================================
    {
        "name": "Rashtriya Krishi Vikas Yojana (RKVY)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Supports agriculture and allied sector development through state-level planning and projects.",
        "eligibility": "Beneficiaries depend on approved state projects and programme components.",
        "category": "Agriculture Development",
        "farmer_need": "Agriculture development",
        "benefit_type": "Agriculture Development Support",
        "link": "https://rkvy.nic.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 15. PM-AASHA
    # ========================================================
    {
        "name": "Pradhan Mantri Annadata Aay Sanrakshan Abhiyan (PM-AASHA)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Supports price assurance and procurement mechanisms for selected agricultural commodities.",
        "eligibility": "Farmers producing notified crops under applicable procurement arrangements.",
        "category": "Price Support",
        "farmer_need": "Better crop price",
        "benefit_type": "Price Support",
        "link": "https://agmarknet.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 16. PM KISAN MAANDHAN
    # ========================================================
    {
        "name": "Pradhan Mantri Kisan Maandhan Yojana (PM-KMY)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Provides pension support to eligible small and marginal farmers after attaining the prescribed age.",
        "eligibility": "Eligible small and marginal farmers meeting scheme conditions.",
        "category": "Pension",
        "farmer_need": "Old-age financial security",
        "benefit_type": "Pension",
        "link": "https://maandhan.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 17. FPO
    # ========================================================
    {
        "name": "Formation and Promotion of Farmer Producer Organizations (FPOs)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Promotes farmer collectives to improve bargaining power, market access and economies of scale.",
        "eligibility": "Eligible farmer groups and producer organizations.",
        "category": "Farmer Organizations",
        "farmer_need": "Collective farming and marketing",
        "benefit_type": "FPO Support",
        "link": "https://sfacindia.com/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 18. PER DROP MORE CROP
    # ========================================================
    {
        "name": "Per Drop More Crop",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Promotes efficient irrigation methods such as drip and sprinkler irrigation.",
        "eligibility": "Eligible farmers under applicable state and programme guidelines.",
        "category": "Irrigation",
        "farmer_need": "Water-saving irrigation",
        "benefit_type": "Micro Irrigation Support",
        "link": "https://pmksy.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 19. NLM
    # ========================================================
    {
        "name": "National Livestock Mission (NLM)",
        "department": "Department of Animal Husbandry and Dairying",
        "purpose": "Supports entrepreneurship, livestock development and productivity improvement.",
        "eligibility": "Eligible livestock farmers, entrepreneurs and approved entities.",
        "category": "Livestock",
        "farmer_need": "Livestock development",
        "benefit_type": "Livestock Support",
        "link": "https://nlm.udyamimitra.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 20. RASHTRIYA GOKUL MISSION
    # ========================================================
    {
        "name": "Rashtriya Gokul Mission",
        "department": "Department of Animal Husbandry and Dairying",
        "purpose": "Promotes development and conservation of indigenous bovine breeds and improved milk productivity.",
        "eligibility": "Eligible dairy farmers, breeding organisations and programme beneficiaries.",
        "category": "Dairy",
        "farmer_need": "Dairy development",
        "benefit_type": "Dairy and Breed Development",
        "link": "https://dahd.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 21. AHIDF
    # ========================================================
    {
        "name": "Animal Husbandry Infrastructure Development Fund (AHIDF)",
        "department": "Department of Animal Husbandry and Dairying",
        "purpose": "Encourages investment in dairy, meat processing, animal feed and related infrastructure.",
        "eligibility": "Eligible entrepreneurs, MSMEs, FPOs and other approved entities.",
        "category": "Animal Husbandry",
        "farmer_need": "Animal husbandry infrastructure",
        "benefit_type": "Infrastructure Finance",
        "link": "https://ahidf.udyamimitra.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 22. PMMSY
    # ========================================================
    {
        "name": "Pradhan Mantri Matsya Sampada Yojana (PMMSY)",
        "department": "Department of Fisheries",
        "purpose": "Supports sustainable fisheries development and improves fisheries productivity and infrastructure.",
        "eligibility": "Eligible fishers, fish farmers, entrepreneurs, FPOs and other approved beneficiaries.",
        "category": "Fisheries",
        "farmer_need": "Fish farming",
        "benefit_type": "Fisheries Support",
        "link": "https://pmmsy.dof.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 23. FIDF
    # ========================================================
    {
        "name": "Fisheries and Aquaculture Infrastructure Development Fund (FIDF)",
        "department": "Department of Fisheries",
        "purpose": "Provides financing support for fisheries and aquaculture infrastructure.",
        "eligibility": "Eligible fisheries entrepreneurs, cooperatives, organisations and approved entities.",
        "category": "Fisheries Infrastructure",
        "farmer_need": "Fisheries infrastructure",
        "benefit_type": "Infrastructure Finance",
        "link": "https://dof.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 24. NBHM
    # ========================================================
    {
        "name": "National Beekeeping and Honey Mission (NBHM)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Promotes scientific beekeeping, honey production and pollination services.",
        "eligibility": "Eligible beekeepers, farmers, entrepreneurs and organisations.",
        "category": "Beekeeping",
        "farmer_need": "Beekeeping and honey production",
        "benefit_type": "Beekeeping Support",
        "link": "https://nbhm.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 25. NATIONAL BAMBOO MISSION
    # ========================================================
    {
        "name": "National Bamboo Mission (NBM)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Promotes bamboo cultivation, processing, value addition and marketing.",
        "eligibility": "Eligible farmers, entrepreneurs and bamboo sector beneficiaries.",
        "category": "Bamboo",
        "farmer_need": "Bamboo cultivation",
        "benefit_type": "Bamboo Development Support",
        "link": "https://nbm.nic.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 26. NATURAL FARMING
    # ========================================================
    {
        "name": "National Mission on Natural Farming (NMNF)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Promotes natural farming practices and reduction of dependence on external agricultural inputs.",
        "eligibility": "Eligible farmers and clusters under applicable programme guidelines.",
        "category": "Natural Farming",
        "farmer_need": "Natural farming",
        "benefit_type": "Natural Farming Support",
        "link": "https://naturalfarming.dac.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 27. NMEO-OP
    # ========================================================
    {
        "name": "National Mission on Edible Oils – Oil Palm (NMEO-OP)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Promotes oil palm cultivation and development of the edible oil value chain.",
        "eligibility": "Farmers in applicable areas and states under programme guidelines.",
        "category": "Oilseeds",
        "farmer_need": "Oil palm cultivation",
        "benefit_type": "Crop Development Support",
        "link": "https://nmeo.dac.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 28. NMEO-OILSEEDS
    # ========================================================
    {
        "name": "National Mission on Edible Oils – Oilseeds (NMEO-Oilseeds)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Supports production and productivity of major oilseed crops.",
        "eligibility": "Eligible oilseed farmers in applicable areas.",
        "category": "Oilseeds",
        "farmer_need": "Oilseed production",
        "benefit_type": "Oilseed Development Support",
        "link": "https://nmeo.dac.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 29. AGRICULTURAL MARKETING INFRASTRUCTURE
    # ========================================================
    {
        "name": "Agricultural Marketing Infrastructure (AMI)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Supports development and improvement of agricultural marketing infrastructure and storage.",
        "eligibility": "Eligible farmers, cooperatives, FPOs and other approved entities.",
        "category": "Marketing",
        "farmer_need": "Storage and market infrastructure",
        "benefit_type": "Marketing Infrastructure Support",
        "link": "https://agmarknet.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 30. MISS
    # ========================================================
    {
        "name": "Modified Interest Subvention Scheme (MISS)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Provides interest-related support on eligible short-term agricultural loans.",
        "eligibility": "Eligible farmers obtaining qualifying agricultural credit through participating institutions.",
        "category": "Credit & Finance",
        "farmer_need": "Lower agricultural credit cost",
        "benefit_type": "Interest Support",
        "link": "https://www.myscheme.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 31. IPM
    # ========================================================
    {
        "name": "Integrated Pest Management (IPM)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Promotes integrated and environmentally responsible management of agricultural pests.",
        "eligibility": "Farmers and agricultural beneficiaries covered by pest management programmes.",
        "category": "Crop Protection",
        "farmer_need": "Pest management",
        "benefit_type": "Crop Protection Support",
        "link": "https://ppqs.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 32. SMAE
    # ========================================================
    {
        "name": "Sub-Mission on Agricultural Extension (SMAE)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Improves access to agricultural information, extension services and farmer training.",
        "eligibility": "Farmers and eligible agricultural extension beneficiaries.",
        "category": "Farmer Training",
        "farmer_need": "Agricultural knowledge",
        "benefit_type": "Extension and Training",
        "link": "https://agriwelfare.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 33. RAD
    # ========================================================
    {
        "name": "Rainfed Area Development (RAD)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Promotes integrated farming systems and productivity improvement in rainfed areas.",
        "eligibility": "Farmers in applicable rainfed areas under programme guidelines.",
        "category": "Rainfed Farming",
        "farmer_need": "Rainfed agriculture",
        "benefit_type": "Integrated Farming Support",
        "link": "https://nmsa.dac.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 34. PM KISAN SAMPADA
    # ========================================================
    {
        "name": "Pradhan Mantri Kisan SAMPADA Yojana",
        "department": "Ministry of Food Processing Industries",
        "purpose": "Supports food processing infrastructure and value addition in agricultural products.",
        "eligibility": "Eligible food processing enterprises, organisations and approved project beneficiaries.",
        "category": "Food Processing",
        "farmer_need": "Food processing and value addition",
        "benefit_type": "Food Processing Support",
        "link": "https://mofpi.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 35. PMFME
    # ========================================================
    {
        "name": "PM Formalisation of Micro Food Processing Enterprises (PMFME)",
        "department": "Ministry of Food Processing Industries",
        "purpose": "Supports formalisation, upgrading and development of micro food processing enterprises.",
        "eligibility": "Eligible micro food processing enterprises and related beneficiaries under scheme guidelines.",
        "category": "Food Processing",
        "farmer_need": "Small food processing business",
        "benefit_type": "Enterprise Support",
        "link": "https://pmfme.mofpi.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 36. OPERATION GREENS
    # ========================================================
    {
        "name": "Operation Greens",
        "department": "Ministry of Food Processing Industries",
        "purpose": "Supports value chains and market infrastructure for selected agricultural and horticultural commodities.",
        "eligibility": "Eligible FPOs, farmers, processors, aggregators and other approved entities.",
        "category": "Agriculture Marketing",
        "farmer_need": "Better value realization",
        "benefit_type": "Value Chain Support",
        "link": "https://mofpi.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 37. ATMA
    # ========================================================
    {
        "name": "Agriculture Technology Management Agency (ATMA)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Provides agricultural extension, demonstrations, training and technology dissemination.",
        "eligibility": "Farmers and farmer groups in participating districts.",
        "category": "Farmer Training",
        "farmer_need": "Training and technology",
        "benefit_type": "Agricultural Extension",
        "link": "https://agriwelfare.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 38. NATIONAL PROJECT ON ORGANIC FARMING
    # ========================================================
    {
        "name": "National Project on Organic Farming",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Promotes organic farming, organic inputs and sustainable agricultural practices.",
        "eligibility": "Eligible farmers, organisations and organic agriculture beneficiaries.",
        "category": "Organic Farming",
        "farmer_need": "Organic inputs and farming",
        "benefit_type": "Organic Agriculture Support",
        "link": "https://pgsindia-ncof.gov.in/",
        "official": True,
        "status": "Active/Programme",
    },

    # ========================================================
    # 39. SOIL HEALTH & FERTILITY
    # ========================================================
    {
        "name": "National Project on Management of Soil Health and Fertility",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Promotes improved soil fertility management and balanced nutrient use.",
        "eligibility": "Farmers and beneficiaries covered under soil health programmes.",
        "category": "Soil & Fertilizer",
        "farmer_need": "Soil fertility",
        "benefit_type": "Soil Fertility Support",
        "link": "https://soilhealth.dac.gov.in/",
        "official": True,
        "status": "Active/Programme",
    },

    # ========================================================
    # 40. CROP RESIDUE MANAGEMENT
    # ========================================================
    {
        "name": "Crop Residue Management Scheme",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Promotes in-situ and ex-situ management of crop residues and reduces crop-residue burning.",
        "eligibility": "Eligible farmers, farmer groups and agricultural machinery beneficiaries in covered areas.",
        "category": "Sustainable Farming",
        "farmer_need": "Crop residue management",
        "benefit_type": "Farm Machinery and Sustainability Support",
        "link": "https://agrimachinery.nic.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 41. SUB-MISSION ON AGROFORESTRY
    # ========================================================
    {
        "name": "Sub-Mission on Agroforestry (SMAF)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Promotes integration of trees with agricultural crops and farming systems.",
        "eligibility": "Eligible farmers and beneficiaries under applicable agroforestry programmes.",
        "category": "Agroforestry",
        "farmer_need": "Agroforestry",
        "benefit_type": "Agroforestry Support",
        "link": "https://agriwelfare.gov.in/",
        "official": True,
        "status": "Active/Programme",
    },

    # ========================================================
    # 42. MOVCDNER
    # ========================================================
    {
        "name": "Mission Organic Value Chain Development for North Eastern Region (MOVCDNER)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Develops certified organic production and value chains in the North Eastern Region.",
        "eligibility": "Eligible farmer groups and value-chain participants in the North Eastern Region.",
        "category": "Organic Farming",
        "farmer_need": "Organic value chain",
        "benefit_type": "Organic Value Chain Support",
        "link": "https://pgsindia-ncof.gov.in/",
        "official": True,
        "status": "Active/Programme",
    },

    # ========================================================
    # 43. LIVESTOCK HEALTH & DISEASE CONTROL
    # ========================================================
    {
        "name": "Livestock Health and Disease Control Programme (LHDCP)",
        "department": "Department of Animal Husbandry and Dairying",
        "purpose": "Supports prevention, control and management of livestock diseases.",
        "eligibility": "Livestock farmers and animals covered under applicable government programmes.",
        "category": "Animal Health",
        "farmer_need": "Livestock disease prevention",
        "benefit_type": "Animal Health Support",
        "link": "https://dahd.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 44. NPDD
    # ========================================================
    {
        "name": "National Programme for Dairy Development (NPDD)",
        "department": "Department of Animal Husbandry and Dairying",
        "purpose": "Strengthens dairy infrastructure, milk procurement and dairy development.",
        "eligibility": "Eligible dairy cooperatives, producer organisations and programme beneficiaries.",
        "category": "Dairy",
        "farmer_need": "Dairy development",
        "benefit_type": "Dairy Infrastructure Support",
        "link": "https://dahd.gov.in/",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 45. DAIRY COOPERATIVE SUPPORT
    # ========================================================
    {
        "name": "Supporting Dairy Cooperatives and Farmer Producer Organisations",
        "department": "Department of Animal Husbandry and Dairying",
        "purpose": "Supports dairy cooperatives and farmer organisations facing financial or operational challenges.",
        "eligibility": "Eligible dairy cooperatives, FPOs and producer organisations under applicable programmes.",
        "category": "Dairy",
        "farmer_need": "Dairy cooperative support",
        "benefit_type": "Financial and Institutional Support",
        "link": "https://dahd.gov.in/",
        "official": True,
        "status": "Active/Programme",
    },

    # ========================================================
    # 46. NATIONAL MISSION FOR PROTEIN SUPPLEMENTS
    # ========================================================
    {
        "name": "National Mission for Protein Supplements",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Supports livestock-related activities and protein-source development under applicable programmes.",
        "eligibility": "Eligible farmers and livestock beneficiaries under applicable programme guidelines.",
        "category": "Livestock",
        "farmer_need": "Livestock productivity",
        "benefit_type": "Livestock Development Support",
        "link": "https://agriwelfare.gov.in/",
        "official": True,
        "status": "Programme",
    },

    # ========================================================
    # 47. CLIMATE RESILIENT AGRICULTURE
    # ========================================================
    {
        "name": "National Innovations in Climate Resilient Agriculture (NICRA)",
        "department": "Indian Council of Agricultural Research (ICAR)",
        "purpose": "Develops and demonstrates climate-resilient agricultural technologies and practices.",
        "eligibility": "Farmers and agricultural communities participating through programme locations and demonstrations.",
        "category": "Climate-Smart Farming",
        "farmer_need": "Climate-resilient farming",
        "benefit_type": "Technology and Demonstration Support",
        "link": "https://icar.gov.in/",
        "official": True,
        "status": "Active/Programme",
    },

    # ========================================================
    # 48. NATIONAL AGRICULTURAL EXTENSION & TECHNOLOGY
    # ========================================================
    {
        "name": "National Mission on Agricultural Extension and Technology",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Improves access to agricultural extension, mechanization and technology services.",
        "eligibility": "Farmers and eligible agricultural beneficiaries under programme components.",
        "category": "Agricultural Technology",
        "farmer_need": "Agricultural technology",
        "benefit_type": "Extension and Technology Support",
        "link": "https://agriwelfare.gov.in/",
        "official": True,
        "status": "Active/Programme",
    },

    # ========================================================
    # 49. RAINFED DEVELOPMENT
    # ========================================================
    {
        "name": "Integrated Farming System for Rainfed Areas",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Promotes integrated crop, livestock and allied farming systems for rainfed agriculture.",
        "eligibility": "Farmers in eligible rainfed regions under applicable programmes.",
        "category": "Rainfed Farming",
        "farmer_need": "Rainfed farm productivity",
        "benefit_type": "Integrated Farming Support",
        "link": "https://nmsa.dac.gov.in/",
        "official": True,
        "status": "Programme",
    },

    # ========================================================
    # 50. NAMO SHETKARI
    # ========================================================
    {
        "name": "Namo Shetkari Mahasanman Nidhi Yojana",
        "department": "Government of Maharashtra",
        "purpose": "Provides additional income support to eligible PM-KISAN farmer families in Maharashtra.",
        "eligibility": "Eligible farmer families under PM-KISAN and Maharashtra scheme conditions.",
        "category": "Maharashtra",
        "farmer_need": "Additional farmer income",
        "benefit_type": "Direct Benefit Transfer",
        "link": "https://www.myscheme.gov.in/schemes/namo-shetkari-mahasanman-nidhi-yojana",
        "official": True,
        "status": "Active",
    },

    # ========================================================
    # 51. CHIEF MINISTER AGRICULTURE & FOOD PROCESSING
    # ========================================================
    {
        "name": "Chief Minister Agriculture and Food Processing Scheme",
        "department": "Government of Maharashtra",
        "purpose": "Supports agriculture and food processing activities in Maharashtra.",
        "eligibility": "Eligible beneficiaries as specified by Maharashtra government programme guidelines.",
        "category": "Maharashtra",
        "farmer_need": "Agriculture and food processing",
        "benefit_type": "Agriculture and Processing Support",
        "link": "https://www.myscheme.gov.in/",
        "official": True,
        "status": "Active/Programme",
    },

    # ========================================================
    # 52. MAHARASHTRA FARM MECHANIZATION
    # ========================================================
    {
        "name": "Maharashtra Agricultural Mechanization Support",
        "department": "Government of Maharashtra - Agriculture Department",
        "purpose": "Supports eligible farmers in accessing agricultural machinery and mechanization services.",
        "eligibility": "Eligible Maharashtra farmers according to applicable agriculture department guidelines.",
        "category": "Maharashtra",
        "farmer_need": "Farm machinery",
        "benefit_type": "Farm Machinery Assistance",
        "link": "https://mahadbt.maharashtra.gov.in/",
        "official": True,
        "status": "State Programme",
    },

    # ========================================================
    # 53. MAHARASHTRA MICRO IRRIGATION
    # ========================================================
    {
        "name": "Maharashtra Micro Irrigation Support",
        "department": "Government of Maharashtra - Agriculture Department",
        "purpose": "Supports eligible farmers in adopting efficient micro-irrigation systems.",
        "eligibility": "Eligible farmers according to applicable Maharashtra government guidelines.",
        "category": "Maharashtra",
        "farmer_need": "Drip and sprinkler irrigation",
        "benefit_type": "Micro Irrigation Assistance",
        "link": "https://mahadbt.maharashtra.gov.in/",
        "official": True,
        "status": "State Programme",
    },

    # ========================================================
    # 54. NATIONAL AGRICULTURE INSURANCE SCHEME
    # ========================================================
    {
        "name": "National Agriculture Insurance Scheme (NAIS)",
        "department": "Ministry of Agriculture and Farmers Welfare",
        "purpose": "Historical crop insurance programme providing protection against crop losses from specified risks.",
        "eligibility": "Eligibility depended on notified crops, areas and programme rules.",
        "category": "Crop Insurance",
        "farmer_need": "Historical crop insurance",
        "benefit_type": "Crop Insurance",
        "link": "https://www.myscheme.gov.in/schemes/nai",
        "official": True,
        "status": "Legacy",
    },

    # ========================================================
    # 55. MUDRA FOR AGRI-ALLIED ENTERPRISES
    # ========================================================
    {
        "name": "Pradhan Mantri MUDRA Yojana (PMMY)",
        "department": "Ministry of Finance",
        "purpose": "Provides institutional credit support to eligible micro enterprises and small businesses, including suitable allied and rural enterprises.",
        "eligibility": "Eligible micro enterprises and entrepreneurs according to lending institution and scheme conditions.",
        "category": "Credit & Finance",
        "farmer_need": "Small agricultural or allied business",
        "benefit_type": "Business Credit",
        "link": "https://www.myscheme.gov.in/schemes/pradhan-mantri-mudra-yojana",
        "official": True,
        "status": "Active",
    },
]


# ============================================================
# BASIC FUNCTIONS
# ============================================================

def get_schemes() -> List[Dict[str, Any]]:
    """
    Return all schemes.
    """
    return SCHEMES.copy()


def get_scheme(scheme_name: str) -> Optional[Dict[str, Any]]:
    """
    Find one scheme by exact or partial name.
    """
    if not scheme_name:
        return None

    query = scheme_name.strip().lower()

    # Exact match first
    for scheme in SCHEMES:
        if scheme["name"].strip().lower() == query:
            return scheme.copy()

    # Partial match
    for scheme in SCHEMES:
        if query in scheme["name"].strip().lower():
            return scheme.copy()

    return None


# ============================================================
# SEARCH
# ============================================================

def search_schemes(query: str) -> List[Dict[str, Any]]:
    """
    Search schemes across important fields.
    """

    if not query:
        return get_schemes()

    query = query.strip().lower()

    results = []

    for scheme in SCHEMES:

        searchable_text = " ".join([
            str(scheme.get("name", "")),
            str(scheme.get("department", "")),
            str(scheme.get("purpose", "")),
            str(scheme.get("eligibility", "")),
            str(scheme.get("category", "")),
            str(scheme.get("farmer_need", "")),
            str(scheme.get("benefit_type", "")),
            str(scheme.get("status", "")),
        ]).lower()

        if query in searchable_text:
            results.append(scheme.copy())

    return results


# ============================================================
# CATEGORY FILTER
# ============================================================

def get_schemes_by_category(category: str) -> List[Dict[str, Any]]:
    """
    Return schemes belonging to a category.
    """

    if not category:
        return get_schemes()

    category = category.strip().lower()

    results = []

    for scheme in SCHEMES:
        scheme_category = str(
            scheme.get("category", "")
        ).strip().lower()

        if scheme_category == category:
            results.append(scheme.copy())

    return results


# ============================================================
# MULTI-CATEGORY SEARCH
# ============================================================

def get_schemes_by_categories(categories: List[str]) -> List[Dict[str, Any]]:
    """
    Return schemes matching any category in the supplied list.
    """

    if not categories:
        return get_schemes()

    normalized = {
        str(category).strip().lower()
        for category in categories
        if category
    }

    return [
        scheme.copy()
        for scheme in SCHEMES
        if str(scheme.get("category", "")).strip().lower() in normalized
    ]


# ============================================================
# RECOMMENDATION ENGINE
# ============================================================

def recommend_schemes(farmer_need: str) -> List[Dict[str, Any]]:
    """
    Recommend schemes according to farmer need.

    Returns schemes sorted by match score.
    """

    if not farmer_need:
        return []

    query = farmer_need.strip().lower()

    recommendations = []

    # Keyword mapping
    keyword_map = {
        "loan": [
            "credit",
            "finance",
            "loan",
            "money",
            "financial",
        ],
        "money": [
            "financial",
            "income",
            "credit",
            "finance",
            "loan",
        ],
        "irrigation": [
            "irrigation",
            "water",
            "drip",
            "sprinkler",
            "solar pump",
        ],
        "water": [
            "irrigation",
            "water",
            "drip",
            "sprinkler",
        ],
        "machinery": [
            "machinery",
            "mechanization",
            "tractor",
            "equipment",
            "farm machine",
        ],
        "tractor": [
            "machinery",
            "mechanization",
            "equipment",
        ],
        "crop insurance": [
            "insurance",
            "crop loss",
            "risk",
            "damage",
        ],
        "insurance": [
            "insurance",
            "crop loss",
            "risk",
        ],
        "organic": [
            "organic",
            "natural",
            "sustainable",
        ],
        "natural farming": [
            "natural",
            "organic",
            "sustainable",
        ],
        "market": [
            "marketing",
            "market",
            "price",
            "selling",
            "storage",
        ],
        "price": [
            "price",
            "marketing",
            "market",
            "procurement",
        ],
        "horticulture": [
            "horticulture",
            "fruit",
            "vegetable",
            "flower",
            "spices",
        ],
        "dairy": [
            "dairy",
            "milk",
            "cattle",
            "cow",
            "buffalo",
        ],
        "livestock": [
            "livestock",
            "animal",
            "goat",
            "sheep",
            "poultry",
        ],
        "fisheries": [
            "fish",
            "fisheries",
            "aquaculture",
            "fish farming",
        ],
        "beekeeping": [
            "bee",
            "beekeeping",
            "honey",
        ],
        "bamboo": [
            "bamboo",
        ],
        "soil": [
            "soil",
            "fertilizer",
            "fertility",
            "nutrient",
        ],
        "pest": [
            "pest",
            "insect",
            "disease",
            "crop protection",
        ],
        "training": [
            "training",
            "education",
            "extension",
            "technology",
        ],
        "food processing": [
            "food processing",
            "processing",
            "value addition",
        ],
        "solar": [
            "solar",
            "energy",
            "pump",
            "electricity",
        ],
        "pension": [
            "pension",
            "old age",
            "retirement",
        ],
        "fpo": [
            "fpo",
            "farmer organization",
            "collective",
        ],
        "maharashtra": [
            "maharashtra",
            "maharashtra farmer",
            "namo shetkari",
        ],
    }

    keywords = keyword_map.get(query, [query])

    for scheme in SCHEMES:

        score = 0

        name = str(scheme.get("name", "")).lower()
        purpose = str(scheme.get("purpose", "")).lower()
        category = str(scheme.get("category", "")).lower()
        farmer_need_text = str(
            scheme.get("farmer_need", "")
        ).lower()
        benefit_type = str(
            scheme.get("benefit_type", "")
        ).lower()

        for keyword in keywords:

            keyword = keyword.lower()

            if keyword in name:
                score += 40

            if keyword in category:
                score += 30

            if keyword in farmer_need_text:
                score += 30

            if keyword in purpose:
                score += 20

            if keyword in benefit_type:
                score += 15

        if score > 0:

            result = scheme.copy()

            # Maximum score = 100
            result["recommendation_score"] = min(score, 100)
            result["match_score"] = min(score, 100)

            recommendations.append(result)

    recommendations.sort(
        key=lambda x: x.get(
            "recommendation_score", 0
        ),
        reverse=True,
    )

    return recommendations


# ============================================================
# SPECIALIZED HELPERS
# ============================================================

def get_machinery_schemes() -> List[Dict[str, Any]]:
    """
    Return machinery and mechanization-related schemes.
    """

    keywords = [
        "machinery",
        "mechanization",
        "equipment",
        "residue",
    ]

    results = []

    for scheme in SCHEMES:

        text = " ".join([
            str(scheme.get("name", "")),
            str(scheme.get("category", "")),
            str(scheme.get("purpose", "")),
            str(scheme.get("farmer_need", "")),
        ]).lower()

        if any(keyword in text for keyword in keywords):
            results.append(scheme.copy())

    return results


def get_financial_schemes() -> List[Dict[str, Any]]:
    """
    Return schemes related to finance, income, credit and pension.
    """

    categories = [
        "Financial Support",
        "Credit & Finance",
        "Pension",
        "Price Support",
    ]

    return get_schemes_by_categories(categories)


def get_irrigation_schemes() -> List[Dict[str, Any]]:
    """
    Return irrigation and water-management schemes.
    """

    keywords = [
        "irrigation",
        "water",
        "drip",
        "sprinkler",
    ]

    results = []

    for scheme in SCHEMES:

        text = " ".join([
            str(scheme.get("name", "")),
            str(scheme.get("category", "")),
            str(scheme.get("purpose", "")),
            str(scheme.get("farmer_need", "")),
        ]).lower()

        if any(keyword in text for keyword in keywords):
            results.append(scheme.copy())

    return results


def get_market_schemes() -> List[Dict[str, Any]]:
    """
    Return agricultural marketing schemes.
    """

    keywords = [
        "market",
        "marketing",
        "price",
        "value chain",
        "storage",
        "procurement",
    ]

    results = []

    for scheme in SCHEMES:

        text = " ".join([
            str(scheme.get("name", "")),
            str(scheme.get("category", "")),
            str(scheme.get("purpose", "")),
            str(scheme.get("farmer_need", "")),
        ]).lower()

        if any(keyword in text for keyword in keywords):
            results.append(scheme.copy())

    return results


def get_horticulture_schemes() -> List[Dict[str, Any]]:
    """
    Return horticulture-related schemes.
    """

    keywords = [
        "horticulture",
        "fruit",
        "vegetable",
        "flower",
        "spices",
        "bamboo",
    ]

    results = []

    for scheme in SCHEMES:

        text = " ".join([
            str(scheme.get("name", "")),
            str(scheme.get("category", "")),
            str(scheme.get("purpose", "")),
            str(scheme.get("farmer_need", "")),
        ]).lower()

        if any(keyword in text for keyword in keywords):
            results.append(scheme.copy())

    return results


def get_livestock_schemes() -> List[Dict[str, Any]]:
    """
    Return livestock and dairy schemes.
    """

    categories = [
        "Livestock",
        "Dairy",
        "Animal Husbandry",
        "Animal Health",
    ]

    return get_schemes_by_categories(categories)


def get_fisheries_schemes() -> List[Dict[str, Any]]:
    """
    Return fisheries-related schemes.
    """

    categories = [
        "Fisheries",
        "Fisheries Infrastructure",
    ]

    return get_schemes_by_categories(categories)


def get_organic_schemes() -> List[Dict[str, Any]]:
    """
    Return organic and natural farming schemes.
    """

    categories = [
        "Organic Farming",
        "Natural Farming",
    ]

    return get_schemes_by_categories(categories)


def get_maharashtra_schemes() -> List[Dict[str, Any]]:
    """
    Return Maharashtra-specific schemes.
    """

    return [
        scheme.copy()
        for scheme in SCHEMES
        if (
            scheme.get("category") == "Maharashtra"
            or "Maharashtra" in str(
                scheme.get("department", "")
            )
        )
    ]


# ============================================================
# CATEGORY LIST
# ============================================================

def get_scheme_categories() -> List[str]:
    """
    Return unique categories in alphabetical order.
    """

    categories = {
        str(scheme.get("category", "")).strip()
        for scheme in SCHEMES
        if scheme.get("category")
    }

    return sorted(categories)


# ============================================================
# STATISTICS
# ============================================================

def get_scheme_statistics() -> Dict[str, Any]:
    """
    Return statistics used by the Government Schemes dashboard.
    """

    total = len(SCHEMES)

    active = sum(
        1
        for scheme in SCHEMES
        if str(
            scheme.get("status", "")
        ).lower() == "active"
    )

    legacy = sum(
        1
        for scheme in SCHEMES
        if str(
            scheme.get("status", "")
        ).lower() == "legacy"
    )

    official = sum(
        1
        for scheme in SCHEMES
        if scheme.get("official") is True
    )

    categories = get_scheme_categories()

    return {
        "total": total,
        "active": active,
        "legacy": legacy,
        "official": official,
        "categories": len(categories),
        "category_list": categories,
    }


# ============================================================
# OFFICIAL CHECK
# ============================================================

def is_official_scheme(
    scheme: Dict[str, Any]
) -> bool:
    """
    Check whether a scheme is marked as official.
    """

    if not scheme:
        return False

    return bool(
        scheme.get("official", False)
    )


# ============================================================
# SCHEME SUMMARY
# ============================================================

def get_scheme_summary(
    scheme_name: str
) -> Optional[Dict[str, Any]]:
    """
    Return a clean summary of one scheme.
    """

    scheme = get_scheme(scheme_name)

    if not scheme:
        return None

    return {
        "name": scheme.get("name"),
        "department": scheme.get("department"),
        "purpose": scheme.get("purpose"),
        "eligibility": scheme.get("eligibility"),
        "category": scheme.get("category"),
        "farmer_need": scheme.get("farmer_need"),
        "benefit_type": scheme.get("benefit_type"),
        "link": scheme.get("link"),
        "official": scheme.get("official", False),
        "status": scheme.get("status", "Unknown"),
    }


# ============================================================
# ACTIVE SCHEMES
# ============================================================

def get_active_schemes() -> List[Dict[str, Any]]:
    """
    Return schemes that are marked Active.
    """

    return [
        scheme.copy()
        for scheme in SCHEMES
        if str(
            scheme.get("status", "")
        ).lower() == "active"
    ]


# ============================================================
# LEGACY SCHEMES
# ============================================================

def get_legacy_schemes() -> List[Dict[str, Any]]:
    """
    Return historical/legacy schemes.
    """

    return [
        scheme.copy()
        for scheme in SCHEMES
        if str(
            scheme.get("status", "")
        ).lower() == "legacy"
    ]


# ============================================================
# TOP RECOMMENDATIONS
# ============================================================

def get_top_recommendations(
    farmer_need: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Return top N recommendations.
    """

    if limit <= 0:
        return []

    recommendations = recommend_schemes(
        farmer_need
    )

    return recommendations[:limit]


# ============================================================
# SCHEME COUNT
# ============================================================

def get_scheme_count() -> int:
    """
    Return total number of schemes.
    """

    return len(SCHEMES)


# ============================================================
# VALIDATION
# ============================================================

def validate_schemes() -> Dict[str, Any]:
    """
    Validate required fields and duplicate scheme names.
    """

    required_fields = [
        "name",
        "department",
        "purpose",
        "eligibility",
        "category",
        "farmer_need",
        "benefit_type",
        "link",
        "official",
        "status",
    ]

    missing_fields = []
    duplicate_names = []

    names_seen = set()

    for index, scheme in enumerate(SCHEMES, start=1):

        for field in required_fields:

            if field not in scheme:
                missing_fields.append({
                    "scheme_index": index,
                    "scheme": scheme.get(
                        "name",
                        f"Scheme {index}"
                    ),
                    "missing_field": field,
                })

        name = str(
            scheme.get("name", "")
        ).strip().lower()

        if name in names_seen:
            duplicate_names.append(
                scheme.get("name")
            )

        names_seen.add(name)

    return {
        "valid": not missing_fields and not duplicate_names,
        "total": len(SCHEMES),
        "missing_fields": missing_fields,
        "duplicate_names": duplicate_names,
    }


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "SCHEMES",

    "get_schemes",
    "get_scheme",
    "search_schemes",

    "get_schemes_by_category",
    "get_schemes_by_categories",
    "get_scheme_categories",

    "recommend_schemes",
    "get_top_recommendations",

    "get_machinery_schemes",
    "get_financial_schemes",
    "get_irrigation_schemes",
    "get_market_schemes",
    "get_horticulture_schemes",
    "get_livestock_schemes",
    "get_fisheries_schemes",
    "get_organic_schemes",
    "get_maharashtra_schemes",

    "get_active_schemes",
    "get_legacy_schemes",

    "get_scheme_statistics",
    "get_scheme_count",

    "is_official_scheme",
    "get_scheme_summary",

    "validate_schemes",
]


# ============================================================
# OPTIONAL LOCAL TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("KisanVision360+ Government Schemes")
    print("=" * 60)

    print(f"Total schemes: {get_scheme_count()}")

    statistics = get_scheme_statistics()

    print(f"Active schemes: {statistics['active']}")
    print(f"Legacy schemes: {statistics['legacy']}")
    print(f"Official schemes: {statistics['official']}")
    print(f"Categories: {statistics['categories']}")

    print("\nCategories:")
    for category in statistics["category_list"]:
        print(f"  - {category}")

    print("\nValidation:")
    print(validate_schemes())

    print("\nTop recommendations for irrigation:")
    for scheme in get_top_recommendations(
        "irrigation",
        5
    ):
        print(
            f"  {scheme['name']} "
            f"({scheme.get('recommendation_score', 0)}%)"
        )

