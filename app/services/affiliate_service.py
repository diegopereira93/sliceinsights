"""
Affiliate URL transformation service.

Transforms store URLs into affiliate links for monetization.
Supports Amazon BR and Mercado Livre initially.
"""

import os
from typing import Optional
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse


class AffiliateService:
    """Service for transforming store URLs into affiliate links."""
    
    def __init__(self):
        # Load affiliate tags from environment
        self.amazon_tag = os.getenv("AFFILIATE_AMAZON_TAG", "")
        self.ml_affiliate_id = os.getenv("AFFILIATE_ML_ID", "")
    
    def transform_url(self, url: str, store_name: Optional[str] = None) -> str:
        """
        Transform a store URL into an affiliate link.
        
        Args:
            url: Original store URL
            store_name: Optional store name hint (for faster matching)
            
        Returns:
            Affiliate URL if applicable, otherwise original URL
        """
        if not url:
            return url
        
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        
        # Amazon (includes amazon.com.br, amazon.com, etc.)
        if "amazon" in hostname and self.amazon_tag:
            return self._transform_amazon(url, parsed)
        
        # Mercado Livre
        if "mercadolivre" in hostname or "mercadolibre" in hostname:
            if self.ml_affiliate_id:
                return self._transform_mercado_livre(url, parsed)
        
        # No transformation available
        return url
    
    def _transform_amazon(self, url: str, parsed) -> str:
        """Add Amazon Associates tag to URL."""
        query_params = parse_qs(parsed.query)
        
        # Remove existing tag if present
        query_params.pop("tag", None)
        
        # Add our affiliate tag
        query_params["tag"] = [self.amazon_tag]
        
        # Rebuild URL
        new_query = urlencode(query_params, doseq=True)
        new_parsed = parsed._replace(query=new_query)
        
        return urlunparse(new_parsed)
    
    def _transform_mercado_livre(self, url: str, parsed) -> str:
        """Add Mercado Livre affiliate parameters."""
        # ML affiliate URLs typically use a redirect pattern
        # For now, append affiliate ID as query parameter
        query_params = parse_qs(parsed.query)
        query_params["aff_id"] = [self.ml_affiliate_id]
        
        new_query = urlencode(query_params, doseq=True)
        new_parsed = parsed._replace(query=new_query)
        
        return urlunparse(new_parsed)
    
    def is_affiliate_enabled(self) -> bool:
        """Check if any affiliate configuration is present."""
        return bool(self.amazon_tag or self.ml_affiliate_id)


# Singleton instance for reuse
_affiliate_service: Optional[AffiliateService] = None


def get_affiliate_service() -> AffiliateService:
    """Get singleton instance of AffiliateService."""
    global _affiliate_service
    if _affiliate_service is None:
        _affiliate_service = AffiliateService()
    return _affiliate_service
