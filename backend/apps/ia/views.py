from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from ia.models_ml import PredicteurVentes, DetecteurAnomalies, RecommandeurProduits, AnalyseurRentabilite

class IAVentesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        nb_jours = int(request.GET.get('jours', 7))
        pred = PredicteurVentes()
        pred.entrainer()
        resultats = pred.predire(nb_jours)
        return Response(resultats)

class IAAnomaliesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        nb_jours = int(request.GET.get('jours', 30))
        det = DetecteurAnomalies()
        resultats = det.analyser(nb_jours)
        return Response(resultats)

class IARecommandationsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        client_id = request.GET.get('client_id')
        reco = RecommandeurProduits()
        reco.entrainer()
        if client_id:
            recos = reco.recommander(int(client_id))
        else:
            recos = reco._top_produits_global(10)
        return Response(recos)

class IARentabiliteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        anal = AnalyseurRentabilite()
        resultats = anal.analyser()
        return Response(resultats)

class IADashboardAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        # Résumé pour le dashboard mobile
        pred = PredicteurVentes()
        alertes = sum(1 for r in pred.predire(7) if r['alerte'])
        
        det = DetecteurAnomalies()
        anomalies = sum(1 for r in det.analyser(30) if r['anomalie'])
        
        anal = AnalyseurRentabilite()
        bcg = anal.analyser()
        stars = sum(1 for r in bcg if r['categorie'] == 'STAR')
        
        return Response({
            'nb_alertes_stock': alertes,
            'nb_anomalies': anomalies,
            'nb_stars': stars,
        })
