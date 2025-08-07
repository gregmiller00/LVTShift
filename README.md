# LVTShift

**LVTShift** is a comprehensive toolkit for analyzing and modeling Land Value Tax (LVT) policy shifts in U.S. counties and cities. Created by the Center for Land Economics ([landeconomics.org](https://landeconomics.org)), this package helps researchers, policymakers, and advocates understand how shifting from traditional property taxes to land value taxes would affect different neighborhoods, property types, and demographic groups.

## What is a Land Value Tax?

A **Land Value Tax** taxes only the value of land, not the buildings or improvements on that land. Unlike traditional property taxes that discourage development by taxing both land and buildings, LVT:

- **Encourages development** - No penalty for improving your property
- **Reduces speculation** - Makes it expensive to hold vacant land
- **Promotes affordable housing** - Removes the tax burden on new construction
- **Generates stable revenue** - Land values are more stable than building values

## What This Package Does

### 🏠 **Property Tax Modeling**
Transform your city's property tax data to model different LVT scenarios:
- **Split-rate taxes** (tax land at 3x, 4x, or any multiple of building rates)
- **Full building abatements** (eliminate taxes on improvements entirely)
- **Graduated exemptions** (phase in LVT with exemptions for smaller properties)
- **Revenue-neutral analysis** (maintain the same total tax revenue)

### 📊 **Data Collection & Processing**
Automatically fetch and process the data you need:
- **Property records** from county GIS systems and open data portals
- **Tax assessment data** including land values, building values, and exemptions
- **Census demographics** (income, race, population) for equity analysis
- **Geographic boundaries** for mapping and spatial analysis

### 📈 **Policy Impact Analysis**
Understand what problems LVT could help solve in your city:
- **Vacant land speculation** - Find concentrated vacant land holdings
- **Underutilized parking lots** - Identify prime development sites sitting empty
- **Development barriers** - Calculate how building taxes discourage construction
- **Housing supply impact** - Estimate how many new housing units LVT could enable

### 🏘️ **Demographic & Equity Analysis**
Ensure your LVT policy is fair and equitable:
- **Income impact analysis** - How does LVT affect different income levels?
- **Racial equity assessment** - Are there disparate impacts by race/ethnicity?
- **Neighborhood analysis** - Which areas benefit vs. bear increased burden?
- **Property type breakdown** - How are different housing types affected?

## Real-World Example: South Bend, Indiana

Our main example analyzes a **4:1 split-rate tax** for South Bend, where land would be taxed at 4 times the rate of buildings. The analysis shows:

- **Single-family homes**: Most see modest tax decreases or increases
- **Vacant land**: Significant tax increases, encouraging development
- **Dense development**: Buildings with high improvement-to-land ratios benefit most
- **Revenue neutral**: Total city tax revenue stays the same

## Getting Started

### 1. Installation
```bash
git clone https://github.com/YOURUSERNAME/LVTShift.git
cd LVTShift
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
```bash
# Copy the template and add your API keys
cp env.template .env
# Then edit .env with your actual API keys
```
You'll need:
- **Census API Key**: Get one free at [api.census.gov/data/key_signup.html](https://api.census.gov/data/key_signup.html)

### 3. Get Your Data
The package can work with any county that provides:
- Property tax assessment data (land value, building value, exemptions)
- Geographic boundaries (for mapping)
- Ideally available through an online GIS portal or API

### 4. Run the Analysis
```bash
cd examples
jupyter notebook southbend.ipynb
```

### 5. Adapt to Your City
The Spokane example (`examples/spokane.ipynb`) shows how to:
- Fetch data from different county systems
- Handle varying data formats and structures
- Customize the analysis for local policy questions

## Key Features by Module

### `census_utils.py` - Demographics Made Easy
```python
from census_utils import get_census_data_with_boundaries

# Get income and demographic data for any county
# API key is automatically loaded from environment variables
census_data, boundaries = get_census_data_with_boundaries(
    fips_code='18141',  # St. Joseph County, IN
    year=2022
)

# Or you can still pass the API key explicitly
census_data, boundaries = get_census_data_with_boundaries(
    fips_code='18141',  # St. Joseph County, IN
    year=2022,
    api_key='your_census_api_key_here'
)
```

### `cloud_utils.py` - Data Fetching
```python
from cloud_utils import get_feature_data_with_geometry

# Fetch property data from county GIS systems
parcels = get_feature_data_with_geometry(
    'Parcel_Civic', 
    'https://maps.saintjosephcounty.com/arcgis/rest/services/'
)
```

### `lvt_utils.py` - Tax Modeling
```python
from lvt_utils import model_split_rate_tax

# Model a 4:1 land-to-building tax ratio
land_rate, building_rate, revenue, results = model_split_rate_tax(
    df=property_data,
    land_value_col='land_value',
    improvement_value_col='improvement_value',
    current_revenue=current_tax_revenue,
    land_improvement_ratio=4
)
```

### `policy_analysis.py` - Problem Identification
```python
from policy_analysis import analyze_vacant_land, analyze_parking_lots

# Find vacant land speculation patterns
vacant_analysis = analyze_vacant_land(
    df=property_data,
    land_value_col='land_value',
    property_type_col='prop_use_desc'
)

# Identify underutilized parking lots
parking_analysis = analyze_parking_lots(
    df=property_data,
    land_value_col='land_value',
    improvement_value_col='improvement_value'
)
```

## Understanding the Output

### Tax Impact Analysis
- **Positive values**: Property owners pay more under LVT
- **Negative values**: Property owners pay less under LVT  
- **Revenue neutral**: Total city revenue remains unchanged

### Property Categories Most Affected
- **Vacant land**: Usually sees largest increases (good - discourages speculation)
- **Dense housing**: Usually sees decreases (good - rewards efficient land use)
- **Parking lots**: Often see increases (good - encourages better land use)
- **Single-family homes**: Mixed impacts depending on lot size vs. house value

### Equity Considerations
The analysis helps you answer:
- Do low-income neighborhoods disproportionately benefit or suffer?
- Are there racial equity implications?
- How can policy be designed to address any inequities?

## Use Cases

### 🏛️ **Policymakers & Government Officials**
- Model revenue-neutral LVT shifts for your jurisdiction
- Understand constituent impacts before proposing legislation
- Generate maps and charts for public presentations

### 🏘️ **Housing Advocates**
- Quantify how property taxes discourage housing development
- Show how LVT could enable thousands of new housing units
- Demonstrate impacts on affordability and housing supply

### 📚 **Researchers & Academics**
- Conduct rigorous analysis of LVT impacts across multiple cities
- Study relationships between land use, taxation, and development patterns
- Publish peer-reviewed research on tax policy outcomes

### 🏗️ **Developers & Planners**
- Understand how tax policy affects development feasibility
- Identify areas where LVT would most encourage development
- Plan for policy changes that could affect land values

## Getting Help

- **Examples**: Start with `examples/southbend.ipynb` for a complete walkthrough
- **Documentation**: Each function includes detailed docstrings
- **Issues**: Report bugs or request features on GitHub
- **Questions**: Contact the Center for Land Economics

## Contributing

We welcome contributions! This toolkit is most useful when it can handle data from many different counties and jurisdictions. If you successfully adapt it to a new area, please share your code and data sources.

## License
MIT License

Copyright (c) 2025 Greg Miller

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
---

*The Center for Land Economics is a nonprofit research organization dedicated to advancing evidence-based land and housing policy. Learn more at [landeconomics.org](https://landeconomics.org).*
