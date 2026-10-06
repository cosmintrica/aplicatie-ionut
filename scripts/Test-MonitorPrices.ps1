[CmdletBinding()]
param([switch]$Offline)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Import-Module (Join-Path $PSScriptRoot 'MonitorPrices.psm1') -Force
$dataDirectory = Join-Path (Split-Path $PSScriptRoot -Parent) 'probe-data'
New-Item -ItemType Directory -Path $dataDirectory -Force | Out-Null
$representativeIds = @('1012187','1013048','1019036','1361463','1011559','1282436','1449689')
$cases = @(
    @{ Name='slatina-three-products'; Lat='44.4281'; Lon='24.3726'; Buffer=5000; Ids=@('1026063','1341915','1027627') },
    @{ Name='slatina-representative'; Lat='44.4281'; Lon='24.3726'; Buffer=5000; Ids=$representativeIds },
    @{ Name='bucharest-representative'; Lat='44.4268'; Lon='26.1025'; Buffer=1000; Ids=$representativeIds },
    @{ Name='slatina-milk-single'; Lat='44.4281'; Lon='24.3726'; Buffer=5000; Ids=@('1012187') }
)
$baseUrl = 'https://monitorulpreturilor.info/pmonsvc/Retail'
if (-not $Offline) {
    $requests = [System.Collections.Generic.List[object]]::new()
    $downloads = @(
        @{ Name='catalog'; Url="$baseUrl/GetCatalogProductsByNameNetwork" },
        @{ Name='networks'; Url="$baseUrl/GetRetailNetworks" }
    )
    foreach ($case in $cases) {
        $ids = $case.Ids -join ','
        $downloads += @{ Name=$case.Name; Url="$baseUrl/GetStoresForProductsByLatLon?lat=$($case.Lat)&lon=$($case.Lon)&buffer=$($case.Buffer)&csvprodids=$ids&OrderBy=price" }
    }
    foreach ($download in $downloads) {
        $watch = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-WebRequest -Uri $download.Url -TimeoutSec 45
        $watch.Stop()
        $response.Content | Set-Content -LiteralPath (Join-Path $dataDirectory ($download.Name + '.xml')) -Encoding utf8
        $requests.Add([pscustomobject]@{
            Name=$download.Name; Url=$download.Url; Status=$response.StatusCode
            Bytes=$response.RawContentLength; ElapsedSeconds=[math]::Round($watch.Elapsed.TotalSeconds, 2)
            CollectedAt=[datetimeoffset]::UtcNow.ToString('o')
        })
    }
    $requests.ToArray() | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $dataDirectory 'requests.json') -Encoding utf8
}
$catalog = @(Read-MonitorCatalog -Path (Join-Path $dataDirectory 'catalog.xml'))
$knownIds = @{}
foreach ($product in $catalog) { $knownIds[$product.CatalogId] = $product.Name }
$caseReports = foreach ($case in $cases) {
    foreach ($id in $case.Ids) {
        if (-not $knownIds.ContainsKey($id)) { throw "Catalog ID $id is absent from the downloaded catalog." }
    }
    $parsed = Read-MonitorPrices -Path (Join-Path $dataDirectory ($case.Name + '.xml')) -CatalogIds $case.Ids
    $products = foreach ($id in $case.Ids) {
        $offers = @($parsed.Offers | Where-Object CatalogId -EQ $id)
        [pscustomobject]@{
            CatalogId=$id; Name=$knownIds[$id]; Quotes=$offers.Count
            LowestReportedPrice=if ($offers.Count) { $offers[0].Price } else { $null }
            LowestPriceStore=if ($offers.Count) { $offers[0].Store } else { $null }
            PriceDates=@($offers | ForEach-Object { $_.PriceDate } | Sort-Object -Unique)
        }
    }
    [pscustomobject]@{ Name=$case.Name; Products=$products; Result=$parsed }
}
$batch = @($caseReports | Where-Object Name -EQ 'slatina-representative')[0]
$single = @($caseReports | Where-Object Name -EQ 'slatina-milk-single')[0]
$batchMilk = @($batch.Result.Offers | Where-Object CatalogId -EQ '1012187' | ForEach-Object { "$($_.StoreId)|$($_.Price)|$($_.PriceDate)" } | Sort-Object)
$singleMilk = @($single.Result.Offers | ForEach-Object { "$($_.StoreId)|$($_.Price)|$($_.PriceDate)" } | Sort-Object)
$differences = @()
if ($batchMilk.Count -and $singleMilk.Count) {
    $differences = @(Compare-Object -ReferenceObject $batchMilk -DifferenceObject $singleMilk)
} elseif ($batchMilk.Count -or $singleMilk.Count) {
    $differences = @([pscustomobject]@{ BatchCount=$batchMilk.Count; SingleCount=$singleMilk.Count })
}
$summary = [pscustomobject]@{
    AnalyzedAt=[datetimeoffset]::UtcNow.ToString('o')
    Mode=if ($Offline) { 'saved responses' } else { 'live HTTP' }
    CatalogCount=$catalog.Count
    EmptyCatalogNames=@($catalog | Where-Object { [string]::IsNullOrWhiteSpace($_.Name) }).Count
    BatchSingleMilkConsistent=$differences.Count -eq 0
    BatchSingleMilkQuoteCount=$singleMilk.Count
    BatchSingleMilkDifferences=$differences
    FoodBasket=Read-MonitorPrices -Path (Join-Path $dataDirectory 'slatina-representative.xml') -CatalogIds @('1012187','1013048','1361463')
    Cases=$caseReports
}
$summary | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $dataDirectory 'summary.json') -Encoding utf8
foreach ($case in $caseReports) {
    Write-Output "$($case.Name): stores=$($case.Result.StoreCount), quotes=$($case.Result.ValidOfferCount), complete baskets=$($case.Result.CompleteBasketCount)"
    $case.Products | Format-Table CatalogId, Name, Quotes, LowestReportedPrice, LowestPriceStore -AutoSize
}
Write-Output "Catalog: $($catalog.Count) records. Batch/single milk consistency: $($summary.BatchSingleMilkConsistent)."
