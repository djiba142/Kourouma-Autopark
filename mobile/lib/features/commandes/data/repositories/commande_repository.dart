import 'package:dio/dio.dart';
import '../../../../core/network/api_client.dart';
import '../../domain/models/commande_model.dart';

class CommandeRepository {
  final ApiClient _apiClient;

  CommandeRepository(this._apiClient);

  Future<List<Commande>> getCommandes({String? statut}) async {
    final response = await _apiClient.dio.get('commandes/', queryParameters: statut != null ? {'statut': statut} : null);
    return (response.data as List).map((e) => Commande.fromJson(e)).toList();
  }

  Future<Commande> getCommandeDetail(int id) async {
    final response = await _apiClient.dio.get('commandes/$id/');
    return Commande.fromJson(response.data);
  }

  Future<void> updateStatus(int id, String status) async {
    await _apiClient.dio.post('commandes/$id/$status/');
  }

  Future<void> registerPayment({
    required int orderId,
    required double montant,
    required String mode,
    String? reference,
    String? proofPath,
  }) async {
    FormData formData = FormData.fromMap({
      'montant': montant,
      'mode_paiement': mode,
      'reference_transaction': reference,
    });

    if (proofPath != null) {
      formData.files.add(MapEntry(
        'preuve_paiement',
        await MultipartFile.fromFile(proofPath),
      ));
    }

    await _apiClient.dio.post('commandes/$orderId/paiement/', data: formData);
  }
}
