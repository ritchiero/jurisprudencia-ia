"""
Integración con Herramientas Externas
Conecta el sistema agéntico con Scraper y Perplexity
"""

import requests
import json
import time
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class SCJNScraperIntegration:
    """
    Integración mejorada con el scraper de SCJN
    Utiliza las técnicas anti-detección probadas anteriormente
    """
    
    def __init__(self):
        self.base_url = "https://sjf2.scjn.gob.mx"
        self.search_url = f"{self.base_url}/busqueda-principal-tesis"
        self.driver = None
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Configura la sesión HTTP con headers realistas"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def _setup_driver(self):
        """Configura Selenium WebDriver con opciones anti-detección"""
        if self.driver:
            return
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent realista
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("WebDriver configurado exitosamente")
        except Exception as e:
            logger.error(f"Error configurando WebDriver: {e}")
            raise
    
    def search_jurisprudencias(self, search_terms: List[str], max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Busca jurisprudencias en SCJN usando términos específicos
        """
        try:
            self._setup_driver()
            
            # Navegar a la página de búsqueda
            self.driver.get(self.search_url)
            time.sleep(2)
            
            # Construir consulta de búsqueda
            search_query = " ".join(search_terms)
            
            # Localizar campo de búsqueda (usando selector actualizado)
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Escriba el tema']"))
            )
            
            # Limpiar y escribir consulta
            search_input.clear()
            search_input.send_keys(search_query)
            time.sleep(1)
            
            # Localizar y hacer clic en botón de búsqueda
            search_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Buscar')]"))
            )
            search_button.click()
            
            # Esperar resultados
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='detalle/tesis']"))
            )
            
            # Extraer resultados
            results = self._extract_search_results(max_results)
            
            logger.info(f"Encontrados {len(results)} resultados para términos: {search_terms}")
            return results
            
        except Exception as e:
            logger.error(f"Error en búsqueda de jurisprudencias: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def _extract_search_results(self, max_results: int) -> List[Dict[str, Any]]:
        """Extrae resultados de la página de búsqueda"""
        results = []
        
        try:
            # Obtener enlaces a jurisprudencias
            result_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='detalle/tesis']")
            
            for i, link in enumerate(result_links[:max_results]):
                try:
                    # Extraer información básica
                    title_element = link.find_element(By.TAG_NAME, "span") if link.find_elements(By.TAG_NAME, "span") else link
                    title = title_element.text.strip()
                    
                    if not title:
                        continue
                    
                    url = link.get_attribute("href")
                    
                    # Extraer número de registro si está disponible
                    registro = self._extract_registro_from_url(url)
                    
                    result = {
                        "id": f"scjn_{registro or i}",
                        "title": title,
                        "url": url,
                        "registro": registro,
                        "source": "SCJN",
                        "extracted_at": datetime.now().isoformat(),
                        "relevance": 0.8 - (i * 0.05)  # Relevancia decreciente por posición
                    }
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.warning(f"Error extrayendo resultado {i}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error extrayendo resultados: {e}")
        
        return results
    
    def _extract_registro_from_url(self, url: str) -> Optional[str]:
        """Extrae número de registro de la URL"""
        try:
            # URL típica: https://sjf2.scjn.gob.mx/detalle/tesis/2023366
            parts = url.split("/")
            if "detalle" in parts and "tesis" in parts:
                tesis_index = parts.index("tesis")
                if tesis_index + 1 < len(parts):
                    return parts[tesis_index + 1]
        except Exception:
            pass
        return None
    
    def get_jurisprudencia_details(self, url: str) -> Optional[Dict[str, Any]]:
        """Obtiene detalles completos de una jurisprudencia"""
        try:
            self._setup_driver()
            self.driver.get(url)
            time.sleep(3)
            
            # Extraer contenido usando BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            details = {
                "url": url,
                "extracted_at": datetime.now().isoformat()
            }
            
            # Extraer título/rubro
            title_element = soup.find('h1') or soup.find('h2')
            if title_element:
                details["rubro"] = title_element.get_text(strip=True)
            
            # Extraer texto completo
            content_divs = soup.find_all('div', class_=lambda x: x and 'texto' in x.lower())
            if content_divs:
                details["texto"] = content_divs[0].get_text(strip=True)
            
            # Extraer metadatos
            metadata_elements = soup.find_all('span', string=lambda x: x and any(
                keyword in x.lower() for keyword in ['época', 'instancia', 'materia', 'tipo', 'fuente']
            ))
            
            for element in metadata_elements:
                if element.parent:
                    text = element.parent.get_text(strip=True)
                    if 'época' in text.lower():
                        details["epoca"] = text
                    elif 'instancia' in text.lower():
                        details["instancia"] = text
                    elif 'materia' in text.lower():
                        details["materia"] = text
                    elif 'tipo' in text.lower():
                        details["tipo"] = text
                    elif 'fuente' in text.lower():
                        details["fuente"] = text
            
            logger.info(f"Detalles extraídos para: {details.get('rubro', 'Sin título')}")
            return details
            
        except Exception as e:
            logger.error(f"Error obteniendo detalles de {url}: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

class PerplexityIntegration:
    """
    Integración con Perplexity AI para búsquedas semánticas avanzadas
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai"
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            })
    
    def search_legal_concepts(self, query: str, context: str = "derecho mexicano") -> Dict[str, Any]:
        """
        Busca conceptos legales usando Perplexity AI
        """
        if not self.api_key:
            # Simulación para desarrollo sin API key
            return self._simulate_perplexity_search(query, context)
        
        try:
            # Construir prompt especializado
            legal_prompt = f"""
            Como experto en {context}, proporciona información sobre: {query}
            
            Incluye:
            1. Definición precisa del concepto
            2. Marco legal aplicable
            3. Jurisprudencia relevante
            4. Términos relacionados
            5. Casos de aplicación práctica
            
            Responde en formato JSON estructurado.
            """
            
            payload = {
                "model": "llama-3.1-sonar-large-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": "Eres un experto en derecho mexicano especializado en jurisprudencia."
                    },
                    {
                        "role": "user",
                        "content": legal_prompt
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.2
            }
            
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                return {
                    "success": True,
                    "content": content,
                    "source": "perplexity",
                    "query": query,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error(f"Error en Perplexity API: {response.status_code}")
                return self._simulate_perplexity_search(query, context)
                
        except Exception as e:
            logger.error(f"Error conectando con Perplexity: {e}")
            return self._simulate_perplexity_search(query, context)
    
    def _simulate_perplexity_search(self, query: str, context: str) -> Dict[str, Any]:
        """Simula respuesta de Perplexity para desarrollo"""
        simulated_responses = {
            "marcas": {
                "definition": "Las marcas son signos distintivos que identifican productos o servicios en el comercio",
                "legal_framework": "Ley de Propiedad Industrial, Código Civil Federal",
                "related_terms": ["signo distintivo", "propiedad industrial", "registro marcario"],
                "jurisprudence": "Jurisprudencia sobre caducidad de marcas por falta de uso"
            },
            "caducidad": {
                "definition": "Pérdida de derechos por el transcurso del tiempo o falta de ejercicio",
                "legal_framework": "Código Civil, Ley de Propiedad Industrial",
                "related_terms": ["prescripción", "vencimiento", "pérdida de vigencia"],
                "jurisprudence": "Criterios sobre caducidad en procedimientos administrativos"
            },
            "reconvencional": {
                "definition": "Demanda que formula el demandado contra el actor en el mismo procedimiento",
                "legal_framework": "Código de Procedimientos Civiles",
                "related_terms": ["contrademanda", "demanda reconvencional", "procedimiento"],
                "jurisprudence": "Requisitos para la procedencia de la reconvención"
            }
        }
        
        # Buscar respuesta simulada
        for key, response in simulated_responses.items():
            if key in query.lower():
                return {
                    "success": True,
                    "content": json.dumps(response, ensure_ascii=False, indent=2),
                    "source": "perplexity_simulation",
                    "query": query,
                    "timestamp": datetime.now().isoformat()
                }
        
        # Respuesta genérica
        return {
            "success": True,
            "content": json.dumps({
                "definition": f"Concepto legal relacionado con: {query}",
                "legal_framework": "Marco legal mexicano aplicable",
                "related_terms": ["término relacionado 1", "término relacionado 2"],
                "jurisprudence": "Jurisprudencia relevante disponible en SCJN"
            }, ensure_ascii=False, indent=2),
            "source": "perplexity_simulation",
            "query": query,
            "timestamp": datetime.now().isoformat()
        }
    
    def analyze_jurisprudence_relevance(self, jurisprudence_text: str, user_query: str) -> Dict[str, Any]:
        """
        Analiza la relevancia de una jurisprudencia respecto a la consulta del usuario
        """
        if not self.api_key:
            return self._simulate_relevance_analysis(jurisprudence_text, user_query)
        
        try:
            analysis_prompt = f"""
            Analiza la relevancia de esta jurisprudencia para la consulta del usuario:
            
            Consulta del usuario: {user_query}
            
            Jurisprudencia: {jurisprudence_text[:1000]}...
            
            Proporciona:
            1. Puntuación de relevancia (0-100)
            2. Conceptos clave que coinciden
            3. Aspectos específicos que responden a la consulta
            4. Recomendaciones de uso
            
            Responde en formato JSON.
            """
            
            payload = {
                "model": "llama-3.1-sonar-large-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": "Eres un experto en análisis de jurisprudencia mexicana."
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.1
            }
            
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                return {
                    "success": True,
                    "analysis": content,
                    "source": "perplexity",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return self._simulate_relevance_analysis(jurisprudence_text, user_query)
                
        except Exception as e:
            logger.error(f"Error en análisis de relevancia: {e}")
            return self._simulate_relevance_analysis(jurisprudence_text, user_query)
    
    def _simulate_relevance_analysis(self, jurisprudence_text: str, user_query: str) -> Dict[str, Any]:
        """Simula análisis de relevancia"""
        # Análisis básico de coincidencias de palabras clave
        query_words = set(user_query.lower().split())
        jurisprudence_words = set(jurisprudence_text.lower().split())
        
        common_words = query_words.intersection(jurisprudence_words)
        relevance_score = min((len(common_words) / len(query_words)) * 100, 100)
        
        analysis = {
            "relevance_score": round(relevance_score, 2),
            "matching_concepts": list(common_words)[:5],
            "specific_aspects": ["Aspectos procedimentales", "Marco legal aplicable"],
            "usage_recommendations": ["Revisar criterios específicos", "Considerar precedentes"]
        }
        
        return {
            "success": True,
            "analysis": json.dumps(analysis, ensure_ascii=False, indent=2),
            "source": "simulation",
            "timestamp": datetime.now().isoformat()
        }

class ExternalToolsManager:
    """
    Gestor centralizado de herramientas externas
    """
    
    def __init__(self, perplexity_api_key: Optional[str] = None):
        self.scraper = SCJNScraperIntegration()
        self.perplexity = PerplexityIntegration(perplexity_api_key)
        self.cache = {}  # Cache simple para resultados
    
    def search_with_scraper(self, terms: List[str], max_results: int = 10) -> List[Dict[str, Any]]:
        """Busca usando el scraper de SCJN"""
        cache_key = f"scraper_{hash(tuple(terms))}_{max_results}"
        
        if cache_key in self.cache:
            logger.info("Usando resultado cacheado del scraper")
            return self.cache[cache_key]
        
        results = self.scraper.search_jurisprudencias(terms, max_results)
        self.cache[cache_key] = results
        
        return results
    
    def enhance_with_perplexity(self, query: str) -> Dict[str, Any]:
        """Mejora búsqueda con Perplexity AI"""
        cache_key = f"perplexity_{hash(query)}"
        
        if cache_key in self.cache:
            logger.info("Usando resultado cacheado de Perplexity")
            return self.cache[cache_key]
        
        result = self.perplexity.search_legal_concepts(query)
        self.cache[cache_key] = result
        
        return result
    
    def get_detailed_jurisprudence(self, url: str) -> Optional[Dict[str, Any]]:
        """Obtiene detalles completos de una jurisprudencia"""
        cache_key = f"details_{hash(url)}"
        
        if cache_key in self.cache:
            logger.info("Usando detalles cacheados")
            return self.cache[cache_key]
        
        details = self.scraper.get_jurisprudencia_details(url)
        if details:
            self.cache[cache_key] = details
        
        return details
    
    def analyze_relevance(self, jurisprudence_text: str, user_query: str) -> Dict[str, Any]:
        """Analiza relevancia usando Perplexity"""
        return self.perplexity.analyze_jurisprudence_relevance(jurisprudence_text, user_query)
    
    def clear_cache(self):
        """Limpia el cache de resultados"""
        self.cache.clear()
        logger.info("Cache de herramientas externas limpiado")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cache"""
        return {
            "cached_items": len(self.cache),
            "cache_keys": list(self.cache.keys())
        }

