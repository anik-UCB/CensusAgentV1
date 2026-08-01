# Census data schema metadata for grounding the LLM agent
# Co-authored with CoCo

SCHEMA_DESCRIPTION = """
You have access to US Census data (American Community Survey 2020, 5-year estimates) 
aggregated at the STATE and COUNTY level. The data comes from the SafeGraph Open Census 
dataset based on Census Block Group data from the US Census Bureau.

Available views in CENSUS_AGENT.PUBLIC:

1. V_POPULATION - Population demographics by state and county
   Columns:
   - STATE_NAME (varchar): Two-letter state abbreviation (e.g., 'CA', 'TX', 'NY')
   - STATE_FIPS (varchar): Two-digit state FIPS code
   - COUNTY (varchar): County name (e.g., 'Los Angeles County')
   - COUNTY_FIPS (varchar): Three-digit county FIPS code
   - TOTAL_POPULATION (number): Total population count
   - MALE_POPULATION (number): Male population count
   - FEMALE_POPULATION (number): Female population count
   - POP_UNDER_18 (number): Population under 18 years old
   - POP_18_TO_34 (number): Population 18-34 years old
   - POP_35_TO_54 (number): Population 35-54 years old
   - POP_55_TO_69 (number): Population 55-69 years old
   - POP_70_PLUS (number): Population 70+ years old
   - WHITE_NON_HISPANIC (number): White non-Hispanic population
   - BLACK_NON_HISPANIC (number): Black non-Hispanic population
   - NATIVE_AMERICAN_NON_HISPANIC (number): Native American non-Hispanic population
   - ASIAN_NON_HISPANIC (number): Asian non-Hispanic population
   - PACIFIC_ISLANDER_NON_HISPANIC (number): Pacific Islander non-Hispanic population
   - HISPANIC_LATINO (number): Hispanic/Latino population (any race)

2. V_INCOME - Household income data by state and county
   Columns:
   - STATE_NAME, STATE_FIPS, COUNTY, COUNTY_FIPS (same as above)
   - TOTAL_HOUSEHOLDS (number): Total number of households
   - HH_UNDER_10K (number): Households with income under $10,000
   - HH_10K_TO_24K (number): Households with income $10,000-$24,999
   - HH_25K_TO_49K (number): Households with income $25,000-$49,999
   - HH_50K_TO_99K (number): Households with income $50,000-$99,999
   - HH_100K_TO_199K (number): Households with income $100,000-$199,999
   - HH_200K_PLUS (number): Households with income $200,000+
   - AVG_MEDIAN_HOUSEHOLD_INCOME (number): Average of block-group-level median household incomes (dollars)
   - AVG_PER_CAPITA_INCOME (number): Average of block-group-level per capita incomes (dollars)

3. V_HOUSING - Housing data by state and county
   Columns:
   - STATE_NAME, STATE_FIPS, COUNTY, COUNTY_FIPS (same as above)
   - TOTAL_HOUSING_UNITS (number): Total housing units
   - OWNER_OCCUPIED_UNITS (number): Owner-occupied housing units
   - RENTER_OCCUPIED_UNITS (number): Renter-occupied housing units
   - AVG_MEDIAN_HOME_VALUE (number): Average of block-group-level median home values (dollars)

4. V_EDUCATION - Educational attainment (population 25+) by state and county
   Columns:
   - STATE_NAME, STATE_FIPS, COUNTY, COUNTY_FIPS (same as above)
   - TOTAL_POP_25_PLUS (number): Total population 25 years and over
   - LESS_THAN_HIGH_SCHOOL (number): Population with less than high school diploma
   - HIGH_SCHOOL_OR_GED (number): Population with high school diploma or GED
   - SOME_COLLEGE (number): Population with some college, no degree
   - ASSOCIATES_DEGREE (number): Population with associate's degree
   - BACHELORS_DEGREE (number): Population with bachelor's degree
   - MASTERS_DEGREE (number): Population with master's degree
   - PROFESSIONAL_OR_DOCTORATE (number): Population with professional or doctorate degree

5. V_EMPLOYMENT - Employment/labor force data by state and county
   Columns:
   - STATE_NAME, STATE_FIPS, COUNTY, COUNTY_FIPS (same as above)
   - POP_16_PLUS (number): Population 16 years and over
   - IN_LABOR_FORCE (number): Population in the labor force
   - EMPLOYED (number): Employed civilian population
   - UNEMPLOYED (number): Unemployed population
   - ARMED_FORCES (number): Armed Forces population
   - NOT_IN_LABOR_FORCE (number): Population not in labor force
   - UNEMPLOYMENT_RATE (number): Unemployment rate as percentage
   - LABOR_FORCE_PARTICIPATION_RATE (number): Labor force participation rate as percentage

6. V_STATE_SUMMARY - Quick state-level population rollup
   Columns: STATE_NAME, STATE_FIPS, TOTAL_POPULATION, MALE_POPULATION, FEMALE_POPULATION,
   POP_UNDER_18, POP_18_TO_34, POP_35_TO_54, POP_55_TO_69, POP_70_PLUS,
   WHITE_NON_HISPANIC, BLACK_NON_HISPANIC, ASIAN_NON_HISPANIC, HISPANIC_LATINO

7. V_STATE_INCOME - State-level income summary (one row per state)
   Columns: STATE_NAME, STATE_FIPS, TOTAL_POPULATION, TOTAL_HOUSEHOLDS, HH_UNDER_10K, HH_10K_TO_24K,
   HH_25K_TO_49K, HH_50K_TO_99K, HH_100K_TO_199K, HH_200K_PLUS,
   MEDIAN_HOUSEHOLD_INCOME (dollars), PER_CAPITA_INCOME (dollars)

8. V_STATE_EMPLOYMENT - State-level employment summary (one row per state)
   Columns: STATE_NAME, STATE_FIPS, TOTAL_POPULATION, POP_16_PLUS, IN_LABOR_FORCE, EMPLOYED, UNEMPLOYED,
   ARMED_FORCES, NOT_IN_LABOR_FORCE, UNEMPLOYMENT_RATE (percentage), LABOR_FORCE_PARTICIPATION_RATE (percentage)

9. V_STATE_EDUCATION - State-level education summary (one row per state)
   Columns: STATE_NAME, STATE_FIPS, TOTAL_POPULATION, TOTAL_POP_25_PLUS, LESS_THAN_HIGH_SCHOOL,
   HIGH_SCHOOL_OR_GED, SOME_COLLEGE, ASSOCIATES_DEGREE, BACHELORS_DEGREE,
   MASTERS_DEGREE, PROFESSIONAL_OR_DOCTORATE, PCT_BACHELORS (percentage), PCT_COLLEGE_OR_HIGHER (percentage)

10. V_STATE_HOUSING - State-level housing summary (one row per state)
    Columns: STATE_NAME, STATE_FIPS, TOTAL_POPULATION, TOTAL_HOUSING_UNITS, OWNER_OCCUPIED_UNITS,
    RENTER_OCCUPIED_UNITS, HOMEOWNERSHIP_RATE (percentage), MEDIAN_HOME_VALUE (dollars)

11. V_COMMUTE - Means of transportation to work by county
    Columns: STATE_NAME, STATE_FIPS, COUNTY, COUNTY_FIPS, TOTAL_WORKERS, DROVE_ALONE,
    CARPOOLED, PUBLIC_TRANSIT, BICYCLE, WALKED, WORKED_FROM_HOME

12. V_STATE_COMMUTE - State-level commute summary (one row per state)
    Columns: STATE_NAME, STATE_FIPS, TOTAL_POPULATION, TOTAL_WORKERS, DROVE_ALONE, CARPOOLED,
    PUBLIC_TRANSIT, BICYCLE, WALKED, WORKED_FROM_HOME, PCT_DROVE_ALONE, PCT_PUBLIC_TRANSIT, PCT_WORK_FROM_HOME

13. V_POVERTY - Poverty status by county
    Columns: STATE_NAME, STATE_FIPS, COUNTY, COUNTY_FIPS, TOTAL_POP_POVERTY_DETERMINED,
    BELOW_POVERTY_LEVEL, AT_OR_ABOVE_POVERTY_LEVEL, POVERTY_RATE (percentage)

14. V_STATE_POVERTY - State-level poverty summary (one row per state)
    Columns: STATE_NAME, STATE_FIPS, TOTAL_POPULATION, TOTAL_POP_POVERTY_DETERMINED,
    BELOW_POVERTY_LEVEL, AT_OR_ABOVE_POVERTY_LEVEL, POVERTY_RATE (percentage)

15. V_HEALTH_INSURANCE - Health insurance coverage by county
    Columns: STATE_NAME, STATE_FIPS, COUNTY, COUNTY_FIPS, TOTAL_POP, TOTAL_UNINSURED,
    TOTAL_INSURED, UNINSURED_RATE (percentage)

16. V_STATE_HEALTH_INSURANCE - State-level health insurance summary (one row per state)
    Columns: STATE_NAME, STATE_FIPS, TOTAL_POPULATION, TOTAL_POP, TOTAL_UNINSURED,
    TOTAL_INSURED, UNINSURED_RATE (percentage)

17. V_INTERNET - Internet/broadband access by county
    Columns: STATE_NAME, STATE_FIPS, COUNTY, COUNTY_FIPS, TOTAL_HOUSEHOLDS,
    WITH_INTERNET_SUBSCRIPTION, INTERNET_NO_SUBSCRIPTION, NO_INTERNET_ACCESS,
    INTERNET_SUBSCRIPTION_RATE (percentage), NO_INTERNET_RATE (percentage)

18. V_STATE_INTERNET - State-level internet access summary (one row per state)
    Columns: STATE_NAME, STATE_FIPS, TOTAL_POPULATION, TOTAL_HOUSEHOLDS,
    WITH_INTERNET_SUBSCRIPTION, NO_INTERNET_ACCESS, INTERNET_SUBSCRIPTION_RATE (percentage), NO_INTERNET_RATE (percentage)

19. V_LANGUAGE - Household language by county
    Columns: STATE_NAME, STATE_FIPS, COUNTY, COUNTY_FIPS, TOTAL_HOUSEHOLDS,
    ENGLISH_ONLY, SPANISH, OTHER_INDO_EUROPEAN, ASIAN_PACIFIC_ISLAND, OTHER_LANGUAGES, PCT_ENGLISH_ONLY (percentage)

20. V_STATE_LANGUAGE - State-level household language (one row per state)
    Columns: STATE_NAME, STATE_FIPS, TOTAL_POPULATION, TOTAL_HOUSEHOLDS,
    ENGLISH_ONLY, SPANISH, OTHER_INDO_EUROPEAN, ASIAN_PACIFIC_ISLAND, OTHER_LANGUAGES, PCT_ENGLISH_ONLY, PCT_SPANISH

21. V_HOUSEHOLD_TYPE - Household type by county
    Columns: STATE_NAME, STATE_FIPS, COUNTY, COUNTY_FIPS, TOTAL_HOUSEHOLDS,
    FAMILY_HOUSEHOLDS, MARRIED_COUPLE_FAMILY, OTHER_FAMILY, NONFAMILY_HOUSEHOLDS, LIVING_ALONE

22. V_STATE_HOUSEHOLD_TYPE - State-level household type (one row per state)
    Columns: STATE_NAME, STATE_FIPS, TOTAL_POPULATION, TOTAL_HOUSEHOLDS,
    FAMILY_HOUSEHOLDS, MARRIED_COUPLE_FAMILY, OTHER_FAMILY, NONFAMILY_HOUSEHOLDS, LIVING_ALONE, PCT_FAMILY_HOUSEHOLDS, PCT_LIVING_ALONE

23. V_VETERANS - Veteran status by county
    Columns: STATE_NAME, STATE_FIPS, COUNTY, COUNTY_FIPS, TOTAL_POP_18_PLUS,
    VETERANS, NONVETERANS, VETERAN_RATE (percentage)

24. V_STATE_VETERANS - State-level veteran status (one row per state)
    Columns: STATE_NAME, STATE_FIPS, TOTAL_POPULATION, TOTAL_POP_18_PLUS,
    VETERANS, NONVETERANS, VETERAN_RATE (percentage)

25. V_SNAP - SNAP/Food stamp receipt by county
    Columns: STATE_NAME, STATE_FIPS, COUNTY, COUNTY_FIPS, TOTAL_HOUSEHOLDS,
    RECEIVED_SNAP, DID_NOT_RECEIVE_SNAP, SNAP_RATE (percentage)

26. V_STATE_SNAP - State-level SNAP receipt (one row per state)
    Columns: STATE_NAME, STATE_FIPS, TOTAL_POPULATION, TOTAL_HOUSEHOLDS,
    RECEIVED_SNAP, DID_NOT_RECEIVE_SNAP, SNAP_RATE (percentage)

27. V_MARITAL_STATUS - Marital status by county
    Columns: STATE_NAME, STATE_FIPS, COUNTY, COUNTY_FIPS, TOTAL_POP_15_PLUS,
    NEVER_MARRIED, NOW_MARRIED, WIDOWED, DIVORCED, MARRIED_RATE (percentage), DIVORCE_RATE (percentage)

28. V_STATE_MARITAL_STATUS - State-level marital status (one row per state)
    Columns: STATE_NAME, STATE_FIPS, TOTAL_POPULATION, TOTAL_POP_15_PLUS,
    NEVER_MARRIED, NOW_MARRIED, WIDOWED, DIVORCED, MARRIED_RATE (percentage),
    NEVER_MARRIED_RATE (percentage), DIVORCE_RATE (percentage)

29. V_SCHOOL_ENROLLMENT - School enrollment by county
    Columns: STATE_NAME, STATE_FIPS, COUNTY, COUNTY_FIPS, TOTAL_POP_3_PLUS,
    ENROLLED_IN_SCHOOL, NURSERY_PRESCHOOL, KINDERGARTEN, GRADES_1_TO_8, GRADES_9_TO_12,
    COLLEGE_UNDERGRADUATE, GRADUATE_PROFESSIONAL, NOT_ENROLLED, ENROLLMENT_RATE (percentage)

30. V_STATE_SCHOOL_ENROLLMENT - State-level school enrollment (one row per state)
    Columns: STATE_NAME, STATE_FIPS, TOTAL_POPULATION, TOTAL_POP_3_PLUS,
    ENROLLED_IN_SCHOOL, NURSERY_PRESCHOOL, KINDERGARTEN, GRADES_1_TO_8, GRADES_9_TO_12,
    COLLEGE_UNDERGRADUATE, GRADUATE_PROFESSIONAL, NOT_ENROLLED, ENROLLMENT_RATE (percentage)

31. V_EARNINGS - Individual earnings by county
    Columns: STATE_NAME, STATE_FIPS, COUNTY, COUNTY_FIPS, TOTAL_POP_WITH_EARNINGS,
    AVG_MEDIAN_EARNINGS, AVG_MEDIAN_EARNINGS_MALE, AVG_MEDIAN_EARNINGS_FEMALE

32. V_STATE_EARNINGS - State-level individual earnings (one row per state)
    Columns: STATE_NAME, STATE_FIPS, TOTAL_POPULATION, TOTAL_POP_WITH_EARNINGS,
    AVG_MEDIAN_EARNINGS, AVG_MEDIAN_EARNINGS_MALE, AVG_MEDIAN_EARNINGS_FEMALE,
    GENDER_EARNINGS_RATIO (female earnings as percentage of male)

33. V_OCCUPATION - Occupation categories by county
    Columns: STATE_NAME, STATE_FIPS, COUNTY, COUNTY_FIPS, TOTAL_CIVILIAN_EMPLOYED,
    MGMT_BUSINESS_SCIENCE_ARTS, SERVICE_OCCUPATIONS, SALES_OFFICE,
    NATURAL_RESOURCES_CONSTRUCTION, PRODUCTION_TRANSPORTATION, PCT_WHITE_COLLAR (percentage)

34. V_STATE_OCCUPATION - State-level occupation categories (one row per state)
    Columns: STATE_NAME, STATE_FIPS, TOTAL_POPULATION, TOTAL_CIVILIAN_EMPLOYED,
    MGMT_BUSINESS_SCIENCE_ARTS, SERVICE_OCCUPATIONS, SALES_OFFICE,
    NATURAL_RESOURCES_CONSTRUCTION, PRODUCTION_TRANSPORTATION,
    PCT_WHITE_COLLAR (percentage), PCT_SERVICE (percentage), PCT_BLUE_COLLAR (percentage)

35. V_MOBILITY - Geographic mobility by county
    Columns: STATE_NAME, STATE_FIPS, COUNTY, COUNTY_FIPS, TOTAL_POP_1_PLUS,
    SAME_HOUSE, MOVED_WITHIN_US, MOVED_SAME_MSA, MOVED_DIFFERENT_MSA,
    MOVED_FROM_ABROAD, MOBILITY_RATE (percentage who moved)

36. V_STATE_MOBILITY - State-level geographic mobility (one row per state)
    Columns: STATE_NAME, STATE_FIPS, TOTAL_POPULATION, TOTAL_POP_1_PLUS,
    SAME_HOUSE, MOVED_WITHIN_US, MOVED_SAME_MSA, MOVED_DIFFERENT_MSA,
    MOVED_FROM_ABROAD, MOBILITY_RATE (percentage who moved)

IMPORTANT NOTES:
- State names are two-letter abbreviations (CA, TX, NY, etc.)
- Use V_STATE_* views for state-level questions (faster, pre-aggregated, no NULLs)
- Use V_POPULATION/V_INCOME/V_HOUSING/V_EDUCATION/V_EMPLOYMENT for county-level detail
- Income and home values are in 2020 inflation-adjusted dollars
- Data source is ACS 2020 5-year estimates
- Puerto Rico (PR) is included; some territories have limited data
- All numeric columns may contain NULL for areas with insufficient sample size
"""

STATE_ABBREVIATIONS = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'DC': 'District of Columbia', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii',
    'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
    'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine',
    'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota',
    'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska',
    'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico',
    'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
    'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'PR': 'Puerto Rico',
    'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota',
    'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
    'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming'
}

AVAILABLE_TOPICS = [
    "population", "demographics", "age", "sex", "gender", "race", "ethnicity",
    "income", "household income", "poverty", "per capita income",
    "housing", "home values", "rent", "homeownership",
    "education", "educational attainment", "college", "high school",
    "employment", "unemployment", "labor force", "jobs",
    "commute", "transportation", "work from home",
    "health insurance", "uninsured",
    "internet", "broadband",
    "language", "english",
    "household type", "family",
    "veterans", "military",
    "SNAP", "food stamps",
    "marital status", "marriage", "divorce",
    "school enrollment", "nursery", "kindergarten", "undergraduate", "graduate school",
    "earnings", "wages", "gender pay gap",
    "occupation", "white collar", "blue collar", "service jobs",
    "mobility", "geographic mobility", "moved", "migration"
]
