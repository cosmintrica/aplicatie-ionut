[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$projectRoot = Split-Path $PSScriptRoot -Parent
Import-Module (Join-Path $projectRoot 'scripts/MonitorPrices.psm1') -Force
$tempRoot = [System.IO.Path]::GetFullPath((Join-Path $projectRoot 'tmp'))
$fixtureDirectory = Join-Path $tempRoot ('parser-tests-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $fixtureDirectory -Force | Out-Null
$script:checks = 0
$script:failures = [System.Collections.Generic.List[string]]::new()

function Assert-Equal {
    param([object]$Actual, [object]$Expected, [string]$Message)
    $script:checks++
    if ($Actual -ne $Expected) {
        $script:failures.Add("${Message}: expected '$Expected', actual '$Actual'.")
    }
}

function Assert-Null {
    param([object]$Actual, [string]$Message)
    $script:checks++
    if ($null -ne $Actual) { $script:failures.Add("${Message}: expected null, actual '$Actual'.") }
}

function Assert-Throws {
    param([scriptblock]$Action, [string]$Message)
    $script:checks++
    try { & $Action | Out-Null; $script:failures.Add("${Message}: expected an exception.") }
    catch { }
}

function Write-Fixture {
    param([string]$Name, [string]$Xml)
    $path = Join-Path $fixtureDirectory ($Name + '.xml')
    Set-Content -LiteralPath $path -Value $Xml -Encoding utf8
    return $path
}

function New-ProductXml {
    param([string]$CatalogId, [string]$RetailId, [string]$Price, [string]$Date = '05.10.2026 08:00')
    $priceElement = if ($Price -eq '__missing__') { '' } else { "<Price>$Price</Price>" }
    $dateElement = if ($Date -eq '__missing__') { '' } else { "<Pricedate>$Date</Pricedate>" }
    return "<Product><Id>$RetailId</Id><Name>Retail product $RetailId</Name><Catprod><Id>$CatalogId</Id><Name>Catalog product $CatalogId</Name></Catprod>$priceElement$dateElement<Unit>BUC</Unit><Promo>false</Promo></Product>"
}

function New-StoreXml {
    param([string]$StoreId, [string[]]$Products)
    return "<RetailStore><Id>$StoreId</Id><Name>Store $StoreId</Name><Retailnetwork><Id>26</Id><Name>Untrusted network name</Name></Retailnetwork><Distance>1.2</Distance><Lastupdate>05.10.2026 08:00</Lastupdate><Basketprice>999.99</Basketprice><Products>$($Products -join '')</Products></RetailStore>"
}

function New-PricesXml {
    param([string[]]$Stores)
    return "<RetailStores xmlns='urn:monitor-fixture'><Items>$($Stores -join '')</Items></RetailStores>"
}

try {
    $catalogPath = Write-Fixture 'catalog' @'
<CatalogProducts xmlns="urn:monitor-fixture"><Items><CatalogProduct><Id>101</Id><Name>Milk</Name></CatalogProduct><CatalogProduct><Id>102</Id><Name>Coffee</Name></CatalogProduct></Items></CatalogProducts>
'@
    $catalog = @(Read-MonitorCatalog -Path $catalogPath)
    Assert-Equal $catalog.Count 2 'Catalog records'
    Assert-Equal $catalog[0].CatalogId '101' 'Catalog IDs are preserved'
    Assert-Equal $catalog[0].Name 'Milk' 'Catalog name'

    $completePath = Write-Fixture 'complete' (New-PricesXml @(
        (New-StoreXml '1' @(
            (New-ProductXml '101' '9001' '4.50'),
            (New-ProductXml '102' '9002' '7.25')
        ))
    ))
    $complete = Read-MonitorPrices -Path $completePath -CatalogIds @('101', '102', '101')
    Assert-Equal $complete.StoreCount 1 'Store count'
    Assert-Equal $complete.ValidOfferCount 2 'Offers use Catprod.Id'
    Assert-Equal $complete.Offers[0].CatalogId '101' 'Catalog ID differs from retail ID'
    Assert-Equal $complete.Offers[0].RetailProductId '9001' 'Retail ID is preserved separately'
    Assert-Equal $complete.Offers[0].NetworkId '26' 'Network identity uses ID'
    Assert-Equal $complete.Baskets[0].RequestedProducts 2 'Duplicate requested IDs count once'
    Assert-Equal $complete.Baskets[0].IsComplete $true 'Complete basket flag'
    Assert-Equal $complete.Baskets[0].CompleteTotal ([decimal]11.75) 'Complete basket total'
    Assert-Equal $complete.Baskets[0].AvailableSubtotal ([decimal]11.75) 'Computed subtotal ignores server Basketprice'

    $retailRequest = Read-MonitorPrices -Path $completePath -CatalogIds @('9001')
    Assert-Equal $retailRequest.ValidOfferCount 0 'Retail Product.Id never matches a catalog request'
    Assert-Equal $retailRequest.ResponseProductRowCount 2 'Response rows count all returned products'
    Assert-Equal $retailRequest.ProductRowCount 0 'Requested rows exclude unrelated catalog products'
    Assert-Equal $retailRequest.UnusableRowCount 0 'Unrelated catalog products are not unusable requested rows'
    Assert-Equal $retailRequest.Baskets[0].IsComplete $false 'Absent requested catalog remains incomplete'
    Assert-Null $retailRequest.Baskets[0].CompleteTotal 'No valid offers have no complete total'

    $invalidPath = Write-Fixture 'invalid' (New-PricesXml @(
        (New-StoreXml '2' @(
            (New-ProductXml '101' '9101' '0'),
            (New-ProductXml '101' '9102' '-2'),
            (New-ProductXml '101' '9103' '__missing__'),
            (New-ProductXml '101' '9104' 'not-a-price'),
            (New-ProductXml '101' '9105' '2.99' '__missing__'),
            (New-ProductXml '101' '9106' '2.99' '31.02.2026 08:00'),
            (New-ProductXml '101' '9107' '2.99' 'not-a-date'),
            (New-ProductXml '102' '9108' '7.25')
        ))
    ))
    $partial = Read-MonitorPrices -Path $invalidPath -CatalogIds @('101', '102')
    Assert-Equal $partial.ProductRowCount 8 'All product rows are counted'
    Assert-Equal $partial.ValidOfferCount 1 'Zero, negative, invalid and undated prices are excluded'
    Assert-Equal $partial.UnusableRowCount 7 'Unavailable rows are counted'
    Assert-Equal $partial.CompleteBasketCount 0 'Incomplete store is excluded from complete basket count'
    Assert-Equal $partial.Baskets[0].AvailableProducts 1 'Partial basket availability'
    Assert-Equal ($partial.Baskets[0].MissingIds -join ',') '101' 'Partial basket missing IDs'
    Assert-Equal $partial.Baskets[0].AvailableSubtotal ([decimal]7.25) 'Partial subtotal is preserved'
    Assert-Null $partial.Baskets[0].CompleteTotal 'Partial basket must never report a complete total'

    $duplicatePath = Write-Fixture 'duplicates' (New-PricesXml @(
        (New-StoreXml '3' @(
            (New-ProductXml '101' '9201' '8.00'),
            (New-ProductXml '101' '9202' '4.50'),
            (New-ProductXml '102' '9203' '7.25')
        ))
    ))
    $duplicate = Read-MonitorPrices -Path $duplicatePath -CatalogIds @('101', '102')
    Assert-Equal $duplicate.ValidOfferCount 3 'Retail alternatives remain inspectable'
    Assert-Equal $duplicate.Baskets[0].AvailableProducts 2 'One basket item per catalog ID'
    Assert-Equal $duplicate.Baskets[0].CompleteTotal ([decimal]11.75) 'Duplicate catalog rows do not inflate total'

    $errorPath = Write-Fixture 'error' '<Error xmlns="urn:monitor-fixture"><Message>Request failed</Message></Error>'
    Assert-Throws { Read-MonitorPrices -Path $errorPath -CatalogIds @('101') } 'XML Error cannot be a successful price response'
    Assert-Throws { Read-MonitorCatalog -Path $errorPath } 'XML Error cannot be a successful catalog response'
    Assert-Throws { Read-MonitorPrices -Path $completePath -CatalogIds @('101,102') } 'Catalog request validates individual numeric IDs'
}
finally {
    $resolvedFixture = [System.IO.Path]::GetFullPath($fixtureDirectory)
    if (-not $resolvedFixture.StartsWith($tempRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'Temporary fixture directory is outside the project tmp directory.'
    }
    Remove-Item -LiteralPath $resolvedFixture -Recurse -Force
}

if ($script:failures.Count) {
    $script:failures | ForEach-Object { Write-Error $_ -ErrorAction Continue }
    throw "$($script:failures.Count) of $script:checks parser checks failed."
}
Write-Output "PASS: $script:checks parser checks (offline, temporary fixtures cleaned)."
