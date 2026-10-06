Set-StrictMode -Version Latest

function Get-XmlText {
    param([System.Xml.XmlNode]$Node, [string]$Path, [System.Xml.XmlNamespaceManager]$Namespace)
    $child = $Node.SelectSingleNode($Path, $Namespace)
    if ($null -eq $child) { return '' }
    return $child.InnerText.Trim()
}

function Read-MonitorCatalog {
    param([Parameter(Mandatory)][string]$Path)
    [xml]$document = Get-Content -LiteralPath $Path -Raw -Encoding utf8
    if ($document.DocumentElement.LocalName -ne 'CatalogProducts') { throw 'Unexpected catalog response.' }
    $ns = [System.Xml.XmlNamespaceManager]::new($document.NameTable)
    $ns.AddNamespace('p', $document.DocumentElement.NamespaceURI)
    foreach ($product in $document.SelectNodes('/p:CatalogProducts/p:Items/p:CatalogProduct', $ns)) {
        [pscustomobject]@{
            CatalogId = Get-XmlText $product 'p:Id' $ns
            Name = Get-XmlText $product 'p:Name' $ns
        }
    }
}

function Read-MonitorPrices {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][ValidatePattern('^\d+$')][string[]]$CatalogIds
    )
    [xml]$document = Get-Content -LiteralPath $Path -Raw -Encoding utf8
    if ($document.DocumentElement.LocalName -ne 'RetailStores') { throw 'Unexpected price response.' }
    $ns = [System.Xml.XmlNamespaceManager]::new($document.NameTable)
    $ns.AddNamespace('p', $document.DocumentElement.NamespaceURI)
    $requested = @($CatalogIds | Select-Object -Unique)
    $offers = [System.Collections.Generic.List[object]]::new()
    $baskets = [System.Collections.Generic.List[object]]::new()
    $rowCount = 0
    $responseRowCount = 0
    foreach ($store in $document.SelectNodes('/p:RetailStores/p:Items/p:RetailStore', $ns)) {
        $storeId = Get-XmlText $store 'p:Id' $ns
        $storeName = Get-XmlText $store 'p:Name' $ns
        $networkId = Get-XmlText $store 'p:Retailnetwork/p:Id' $ns
        $storeOffers = [System.Collections.Generic.List[object]]::new()
        foreach ($product in $store.SelectNodes('p:Products/p:Product', $ns)) {
            $responseRowCount++
            $catalogId = Get-XmlText $product 'p:Catprod/p:Id' $ns
            if ($catalogId -notin $requested) { continue }
            $rowCount++
            $priceText = Get-XmlText $product 'p:Price' $ns
            $dateText = Get-XmlText $product 'p:Pricedate' $ns
            [decimal]$price = 0
            [datetime]$priceDate = [datetime]::MinValue
            $numeric = [decimal]::TryParse($priceText, [System.Globalization.NumberStyles]::Number,
                [cultureinfo]::InvariantCulture, [ref]$price)
            $dated = [datetime]::TryParseExact($dateText, 'dd.MM.yyyy HH:mm',
                [cultureinfo]::InvariantCulture, [System.Globalization.DateTimeStyles]::None, [ref]$priceDate)
            # Zero/missing/invalid data are unavailable quotes, never free products.
            if (-not $numeric -or $price -le 0 -or -not $dated) { continue }
            $offer = [pscustomobject]@{
                StoreId = $storeId
                Store = $storeName
                NetworkId = $networkId
                CatalogId = $catalogId
                CatalogName = Get-XmlText $product 'p:Catprod/p:Name' $ns
                RetailProductId = Get-XmlText $product 'p:Id' $ns
                RetailName = Get-XmlText $product 'p:Name' $ns
                Price = $price
                PriceDate = $dateText
                Unit = Get-XmlText $product 'p:Unit' $ns
                Promo = Get-XmlText $product 'p:Promo' $ns
            }
            $offers.Add($offer)
            $storeOffers.Add($offer)
        }
        # One reported item per catalog ID. Unit/pack equivalence must be checked
        # before using this arithmetic as a payable shopping cart.
        $bestPerId = @($storeOffers | Group-Object CatalogId | ForEach-Object {
            $_.Group | Sort-Object Price | Select-Object -First 1
        })
        $availableIds = @($bestPerId | ForEach-Object { $_.CatalogId })
        $missingIds = @($requested | Where-Object { $_ -notin $availableIds })
        [decimal]$subtotal = 0
        foreach ($offer in $bestPerId) { $subtotal += $offer.Price }
        $baskets.Add([pscustomobject]@{
            StoreId = $storeId
            Store = $storeName
            NetworkId = $networkId
            DistanceKm = Get-XmlText $store 'p:Distance' $ns
            StoreLastUpdate = Get-XmlText $store 'p:Lastupdate' $ns
            ServerBasketPrice = Get-XmlText $store 'p:Basketprice' $ns
            RequestedProducts = $requested.Count
            AvailableProducts = $availableIds.Count
            MissingIds = $missingIds
            AvailableSubtotal = $subtotal
            IsComplete = $missingIds.Count -eq 0
            CompleteTotal = if ($missingIds.Count -eq 0) { $subtotal } else { $null }
        })
    }
    [pscustomobject]@{
        SourceFile = [System.IO.Path]::GetFullPath($Path)
        StoreCount = $baskets.Count
        ResponseProductRowCount = $responseRowCount
        ProductRowCount = $rowCount
        ValidOfferCount = $offers.Count
        UnusableRowCount = $rowCount - $offers.Count
        CompleteBasketCount = @($baskets | Where-Object IsComplete).Count
        Offers = @($offers.ToArray() | Sort-Object CatalogId, Price, StoreId)
        Baskets = @($baskets.ToArray() | Sort-Object @{Expression='AvailableProducts';Descending=$true}, AvailableSubtotal)
    }
}

Export-ModuleMember -Function Read-MonitorCatalog, Read-MonitorPrices
