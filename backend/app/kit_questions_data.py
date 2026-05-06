"""Chestionare 32 întrebări pe kit - din documentele metodologice."""

RESPONSABIL_OPTS = ["administrator", "delegat", "contabil"]

# Mapare: trigger_nu = riscuri activate când răspunsul e NU, trigger_da = când e DA
# Coduri risc: R1-R50

KIT_ADMINISTRATIV = {
    "code": "internal_fiscal_procedures",
    "name": "Risc general administrativ",
    "description": "Responsabilitate, trasabilitate și fluxuri interne pentru relația cu contabilul.",
    "sections": [
        {
            "title": "Riscuri informaționale",
            "description": "Calitatea informațiilor administrative primite de contabil",
            "questions": [
                {
                    "key": "q1_1",
                    "label": "Documentele administrative ale societății (act constitutiv, modificări, mandate) sunt transmise contabilului complet și la timp?",
                    "trigger_nu": ["R1", "R2"],
                    "trigger_da": [],
                    "responsabil_label": "Responsabil transmitere",
                },
                {
                    "key": "q1_2",
                    "label": "Există situații în care modificările societare (administrator, sediu, activitate) sunt comunicate contabilului după efectuarea lor?",
                    "trigger_nu": [],
                    "trigger_da": ["R4", "R5"],
                    "responsabil_label": "Responsabil informare",
                },
                {
                    "key": "q1_3",
                    "label": "Există documente administrative lipsă sau neactualizate?",
                    "trigger_nu": [],
                    "trigger_da": ["R6", "R1"],
                    "responsabil_label": "Responsabil documentare",
                },
                {
                    "key": "q1_4",
                    "label": "Există o procedură internă pentru transmiterea documentelor administrative către contabilitate?",
                    "trigger_nu": ["R28"],
                    "trigger_da": [],
                    "responsabil_label": "Responsabil procedură",
                },
            ],
        },
        {
            "title": "Riscuri tranzacționale",
            "description": "Credite, leasing, flotă auto",
            "questions": [
                {
                    "key": "q2_1",
                    "label": "Societatea are credite bancare sau alte finanțări active?",
                    "trigger_nu": [],
                    "trigger_da": ["R8", "R14"],
                    "responsabil_label": "Responsabil monitorizare",
                },
                {
                    "key": "q2_2",
                    "label": "Societatea are contracte de leasing în derulare?",
                    "trigger_nu": [],
                    "trigger_da": ["R8", "R24"],
                    "responsabil_label": "Responsabil gestionare",
                },
                {
                    "key": "q2_3",
                    "label": "Societatea deține sau utilizează flotă auto în activitate?",
                    "trigger_nu": [],
                    "trigger_da": ["R14", "R18"],
                    "responsabil_label": "Responsabil administrare",
                },
                {
                    "key": "q2_4",
                    "label": "Există vehicule utilizate și în scop personal sau mixt?",
                    "trigger_nu": [],
                    "trigger_da": ["R18", "R15"],
                    "responsabil_label": "Responsabil utilizare",
                },
            ],
        },
        {
            "title": "Riscuri fiscale",
            "description": "Impact fiscal al deciziilor administrative",
            "questions": [
                {
                    "key": "q3_1",
                    "label": "Există cheltuieli generate de utilizarea vehiculelor societății care pot avea caracter mixt?",
                    "trigger_nu": [],
                    "trigger_da": ["R18"],
                    "responsabil_label": "Responsabil justificare",
                },
                {
                    "key": "q3_2",
                    "label": "Există contracte de leasing sau finanțare cu tratament fiscal complex?",
                    "trigger_nu": [],
                    "trigger_da": ["R15", "R20"],
                    "responsabil_label": "Responsabil tratament fiscal",
                },
                {
                    "key": "q3_3",
                    "label": "Există diferențe între utilizarea reală a activelor și tratamentul fiscal aplicat?",
                    "trigger_nu": [],
                    "trigger_da": ["R19", "R20"],
                    "responsabil_label": "Responsabil evaluare",
                },
                {
                    "key": "q3_4",
                    "label": "Există situații în care cheltuielile administrative sunt dificil de documentat fiscal?",
                    "trigger_nu": [],
                    "trigger_da": ["R18", "R3"],
                    "responsabil_label": "Responsabil justificare",
                },
            ],
        },
        {
            "title": "Riscuri contabile",
            "questions": [
                {
                    "key": "q4_1",
                    "label": "Există active ale societății pentru care nu există documente complete de achiziție?",
                    "trigger_nu": [],
                    "trigger_da": ["R1", "R23"],
                    "responsabil_label": "Responsabil documentare",
                },
                {
                    "key": "q4_2",
                    "label": "Există bunuri utilizate în activitate fără evidență contabilă clară?",
                    "trigger_nu": [],
                    "trigger_da": ["R24", "R25"],
                    "responsabil_label": "Responsabil evidență",
                },
                {
                    "key": "q4_3",
                    "label": "Există active sau contracte administrative care nu sunt reflectate corect în contabilitate?",
                    "trigger_nu": [],
                    "trigger_da": ["R25", "R26"],
                    "responsabil_label": "Responsabil corelare",
                },
                {
                    "key": "q4_4",
                    "label": "Există evidențe administrative separate care nu sunt corelate cu contabilitatea?",
                    "trigger_nu": [],
                    "trigger_da": ["R27"],
                    "responsabil_label": "Responsabil corelare",
                },
            ],
        },
        {
            "title": "Riscuri operaționale",
            "description": "Organizarea firmei",
            "questions": [
                {
                    "key": "q5_1",
                    "label": "Există proceduri interne pentru gestionarea documentelor administrative?",
                    "trigger_nu": ["R28"],
                    "trigger_da": [],
                    "responsabil_label": "Responsabil procedură",
                },
                {
                    "key": "q5_2",
                    "label": "Există o persoană desemnată pentru relația administrativă cu contabilul?",
                    "trigger_nu": ["R32"],
                    "trigger_da": [],
                    "responsabil_label": "Responsabil comunicare",
                },
                {
                    "key": "q5_3",
                    "label": "Documentele societății sunt arhivate într-un sistem organizat?",
                    "trigger_nu": ["R29"],
                    "trigger_da": [],
                    "responsabil_label": "Responsabil arhivare",
                },
                {
                    "key": "q5_4",
                    "label": "Există control intern asupra documentelor administrative importante?",
                    "trigger_nu": ["R30"],
                    "trigger_da": [],
                    "responsabil_label": "Responsabil control",
                },
            ],
        },
        {
            "title": "Riscuri juridice",
            "questions": [
                {
                    "key": "q6_1",
                    "label": "Actul constitutiv al societății este actualizat conform structurii actuale?",
                    "trigger_nu": ["R35"],
                    "trigger_da": [],
                    "responsabil_label": "Responsabil actualizare",
                },
                {
                    "key": "q6_2",
                    "label": "Mandatele administratorilor sunt valabile și înregistrate?",
                    "trigger_nu": ["R34"],
                    "trigger_da": [],
                    "responsabil_label": "Responsabil verificare",
                },
                {
                    "key": "q6_3",
                    "label": "Există modificări societare neînregistrate la registrul comerțului?",
                    "trigger_nu": [],
                    "trigger_da": ["R34", "R36"],
                    "responsabil_label": "Responsabil înregistrare",
                },
                {
                    "key": "q6_4",
                    "label": "Există litigii sau dispute juridice care pot afecta activitatea societății?",
                    "trigger_nu": [],
                    "trigger_da": ["R37"],
                    "responsabil_label": "Responsabil gestionare",
                },
            ],
        },
        {
            "title": "Riscuri de conformare",
            "description": "Suspendare / inactivare",
            "questions": [
                {
                    "key": "q7_1",
                    "label": "Societatea respectă obligațiile administrative privind actualizarea datelor societare?",
                    "trigger_nu": ["R40"],
                    "trigger_da": [],
                    "responsabil_label": "Responsabil conformare",
                },
                {
                    "key": "q7_2",
                    "label": "Există situații în care societatea nu depune la timp documentele obligatorii?",
                    "trigger_nu": [],
                    "trigger_da": ["R40", "R42"],
                    "responsabil_label": "Responsabil monitorizare",
                },
                {
                    "key": "q7_3",
                    "label": "Există riscul suspendării activității societății din motive administrative?",
                    "trigger_nu": [],
                    "trigger_da": ["R39"],
                    "responsabil_label": "Responsabil prevenire",
                },
                {
                    "key": "q7_4",
                    "label": "Există riscul inactivării societății din motive administrative sau fiscale?",
                    "trigger_nu": [],
                    "trigger_da": ["R39", "R38"],
                    "responsabil_label": "Responsabil prevenire",
                },
            ],
        },
        {
            "title": "Riscuri reputaționale",
            "questions": [
                {
                    "key": "q8_1",
                    "label": "Există situații în care partenerii solicită documente administrative care nu pot fi furnizate imediat?",
                    "trigger_nu": [],
                    "trigger_da": ["R49"],
                    "responsabil_label": "Responsabil gestionare",
                },
                {
                    "key": "q8_2",
                    "label": "Există contracte sau documente administrative incomplete în relația cu partenerii?",
                    "trigger_nu": [],
                    "trigger_da": ["R36"],
                    "responsabil_label": "Responsabil documentare",
                },
                {
                    "key": "q8_3",
                    "label": "Există întârzieri administrative care afectează relația cu instituții sau parteneri?",
                    "trigger_nu": [],
                    "trigger_da": ["R49"],
                    "responsabil_label": "Responsabil gestionare",
                },
                {
                    "key": "q8_4",
                    "label": "Există situații în care lipsa documentelor administrative afectează imaginea societății?",
                    "trigger_nu": [],
                    "trigger_da": ["R50"],
                    "responsabil_label": "Responsabil gestionare",
                },
            ],
        },
    ],
}

# Kit Risc Extins folosește același chestionar generic din "risc extins chetionar" - 32 întrebări
# Pentru MVP, Kit Risc Extins va folosi același set ca Administrativ (extindem mai târziu cu întrebări complete)
KIT_RISC_EXTINS_QUESTIONS = [
    {
        "section": 1,
        "title": "Riscuri informaționale",
        "questions": [
            {
                "key": "re1_1",
                "label": "Documentele justificative sunt transmise contabilului complet și la timp?",
                "trigger_nu": ["R1", "R2"],
                "trigger_da": [],
            },
            {
                "key": "re1_2",
                "label": "Există situații în care tranzacțiile sunt comunicate contabilului după efectuarea lor?",
                "trigger_nu": [],
                "trigger_da": ["R4", "R5"],
            },
            {
                "key": "re1_3",
                "label": "Există tranzacții pentru care explicația economică nu este documentată?",
                "trigger_nu": [],
                "trigger_da": ["R3"],
            },
            {
                "key": "re1_4",
                "label": "Există proceduri interne pentru colectarea și transmiterea documentelor către contabilitate?",
                "trigger_nu": ["R28"],
                "trigger_da": [],
            },
        ],
    },
    {
        "section": 2,
        "title": "Riscuri tranzacționale",
        "questions": [
            {
                "key": "re2_1",
                "label": "Societatea desfășoară tranzacții cu persoane sau firme afiliate?",
                "trigger_nu": [],
                "trigger_da": ["R8"],
            },
            {
                "key": "re2_2",
                "label": "Societatea efectuează tranzacții internaționale (UE sau extra UE)?",
                "trigger_nu": [],
                "trigger_da": ["R9", "R10"],
            },
            {
                "key": "re2_3",
                "label": "Există tranzacții ocazionale în afara activității obișnuite a societății?",
                "trigger_nu": [],
                "trigger_da": ["R11"],
            },
            {
                "key": "re2_4",
                "label": "Există tranzacții cu numerar semnificative sau frecvente?",
                "trigger_nu": [],
                "trigger_da": ["R12"],
            },
        ],
    },
    {
        "section": 3,
        "title": "Riscuri fiscale",
        "questions": [
            {
                "key": "re3_1",
                "label": "Societatea desfășoară operațiuni cu TVA complexe (import, export, intracomunitar)?",
                "trigger_nu": [],
                "trigger_da": ["R15"],
            },
            {
                "key": "re3_2",
                "label": "Există cheltuieli care pot avea caracter personal sau mixt?",
                "trigger_nu": [],
                "trigger_da": ["R18"],
            },
            {
                "key": "re3_3",
                "label": "Societatea utilizează scheme fiscale sau optimizări fiscale speciale?",
                "trigger_nu": [],
                "trigger_da": ["R21"],
            },
            {
                "key": "re3_4",
                "label": "Există diferențe frecvente între situația fiscală și situația contabilă?",
                "trigger_nu": [],
                "trigger_da": ["R20"],
            },
        ],
    },
    {
        "section": 4,
        "title": "Riscuri contabile",
        "questions": [
            {
                "key": "re4_1",
                "label": "Există tranzacții care necesită estimări contabile (provizioane, ajustări)?",
                "trigger_nu": [],
                "trigger_da": ["R22"],
            },
            {
                "key": "re4_2",
                "label": "Există active sau stocuri care necesită evaluări periodice?",
                "trigger_nu": [],
                "trigger_da": ["R23"],
            },
            {
                "key": "re4_3",
                "label": "Există tranzacții complexe care necesită interpretare contabilă?",
                "trigger_nu": [],
                "trigger_da": ["R24"],
            },
            {
                "key": "re4_4",
                "label": "Societatea utilizează mai multe sisteme sau evidențe contabile interne?",
                "trigger_nu": [],
                "trigger_da": ["R27"],
            },
        ],
    },
    {
        "section": 5,
        "title": "Riscuri operaționale",
        "questions": [
            {
                "key": "re5_1",
                "label": "Există proceduri interne pentru aprobarea cheltuielilor?",
                "trigger_nu": ["R28"],
                "trigger_da": [],
            },
            {
                "key": "re5_2",
                "label": "Există separarea responsabilităților între emiterea, aprobarea și plata tranzacțiilor?",
                "trigger_nu": ["R29"],
                "trigger_da": [],
            },
            {
                "key": "re5_3",
                "label": "Societatea are un sistem de arhivare organizat pentru documente?",
                "trigger_nu": ["R29"],
                "trigger_da": [],
            },
            {
                "key": "re5_4",
                "label": "Există persoane desemnate pentru comunicarea cu contabilul?",
                "trigger_nu": ["R32"],
                "trigger_da": [],
            },
        ],
    },
    {
        "section": 6,
        "title": "Riscuri juridice",
        "questions": [
            {
                "key": "re6_1",
                "label": "Tranzacțiile importante sunt susținute de contracte scrise?",
                "trigger_nu": ["R34"],
                "trigger_da": [],
            },
            {
                "key": "re6_2",
                "label": "Contractele sunt revizuite periodic?",
                "trigger_nu": ["R35"],
                "trigger_da": [],
            },
            {
                "key": "re6_3",
                "label": "Există litigii sau dispute comerciale în desfășurare?",
                "trigger_nu": [],
                "trigger_da": ["R37"],
            },
            {
                "key": "re6_4",
                "label": "Există tranzacții bazate doar pe înțelegeri verbale?",
                "trigger_nu": [],
                "trigger_da": ["R34"],
            },
        ],
    },
    {
        "section": 7,
        "title": "Riscuri de conformare",
        "questions": [
            {
                "key": "re7_1",
                "label": "Există verificări interne înainte de depunerea declarațiilor fiscale?",
                "trigger_nu": ["R42"],
                "trigger_da": [],
            },
            {
                "key": "re7_2",
                "label": "Societatea respectă termenele legale pentru raportări?",
                "trigger_nu": ["R40"],
                "trigger_da": [],
            },
            {
                "key": "re7_3",
                "label": "Există proceduri pentru corectarea erorilor contabile sau fiscale?",
                "trigger_nu": ["R42"],
                "trigger_da": [],
            },
            {
                "key": "re7_4",
                "label": "Există verificări periodice ale evidențelor contabile?",
                "trigger_nu": ["R42"],
                "trigger_da": [],
            },
        ],
    },
    {
        "section": 8,
        "title": "Riscuri reputaționale",
        "questions": [
            {
                "key": "re8_1",
                "label": "Societatea verifică partenerii comerciali înainte de colaborare?",
                "trigger_nu": ["R50"],
                "trigger_da": [],
            },
            {
                "key": "re8_2",
                "label": "Există tranzacții cu parteneri necunoscuți sau noi?",
                "trigger_nu": [],
                "trigger_da": ["R46"],
            },
            {
                "key": "re8_3",
                "label": "Există tranzacții frecvente cu societăți nou înființate?",
                "trigger_nu": [],
                "trigger_da": ["R46"],
            },
            {
                "key": "re8_4",
                "label": "Există tranzacții cu parteneri care au avut probleme fiscale sau financiare?",
                "trigger_nu": [],
                "trigger_da": ["R46", "R48"],
            },
        ],
    },
]
