import 'package:dio/dio.dart';
import 'package:autopieces_pro/features/commandes/domain/models/commande_model.dart';

class CommandeService {
  final Dio _dio = Dio(BaseOptions(baseUrl: 'http://10.0.2.2:8000/api/')); // Mapping for Android Emulator

  Future<List<Commande>> getOrders({String? status}) async {
    final response = await _dio.get('commandes/', queryParameters: status != null ? {'statut': status} : {});
    return (response.data as List).map((json) => Commande.fromJson(json)).toList();
  }

  Future<Commande> createOrder({
    required int? clientId,
    required List<Map<String, dynamic>> lines,
    required double remise,
    required String typeRemise,
    required String typeVente,
    Map<String, dynamic>? initialPayment,
  }) async {
    final data = {
      "client": clientId,
      "lignes": lines,
      "remise": remise,
      "type_remise": typeRemise,
      "type_vente": typeVente,
      if (initialPayment != null) "paiement": initialPayment,
    };
    
    final response = await _dio.post('commandes/', data: data);
    return Commande.fromJson(response.data);
  }

  Future<void> updateStatus(int orderId, String action) async {
    await _dio.post('commandes/$orderId/$action/');
  }

  Future<void> addPayment(int orderId, double montant, String mode) async {
    await _dio.post('commandes/$orderId/paiement/', data: {
      "montant": montant,
      "mode_paiement": mode
    });
  }
}
