from typing import Dict, Any, List
from datetime import datetime
from app.models.response_models import VisualizationData, TimelineEvent

class VisualizationGenerator:
    """Generate data for visualizations"""
    
    def generate_chart_data(self, analysis_result: Dict) -> VisualizationData:
        """Generate structured visualization data"""
        return VisualizationData(
            source_breakdown=self._prepare_source_chart(analysis_result),
            timeline=self._prepare_timeline_chart(analysis_result),
            component_frequencies=self._prepare_frequency_chart(analysis_result),
            reliability_scores=self._prepare_reliability_chart(analysis_result)
        )
    
    def _prepare_source_chart(self, analysis_result: Dict) -> Dict[str, float]:
        """Prepare source distribution data"""
        sources = analysis_result.get("sources", {})
        total = sum(sources.values())
        return {
            source: count/total 
            for source, count in sources.items()
        } if total else {}
    
    def _prepare_timeline_chart(self, analysis_result: Dict) -> List[TimelineEvent]:
        """Prepare timeline visualization data"""
        events = []
        for article in analysis_result.get("articles", []):
            events.append(TimelineEvent(
                timestamp=article.get("published_at", datetime.now()),
                title=article.get("title", ""),
                source=article.get("source", ""),
                relevance=article.get("relevance_score", 0.5)
            ))
        return sorted(events, key=lambda x: x.timestamp)
    
    def _prepare_frequency_chart(self, analysis_result: Dict) -> Dict[str, int]:
        """Prepare component frequency data"""
        return analysis_result.get("frequencies", {})
    
    def _prepare_reliability_chart(self, analysis_result: Dict) -> Dict[str, float]:
        """Prepare source reliability scores"""
        return analysis_result.get("reliability_scores", {})