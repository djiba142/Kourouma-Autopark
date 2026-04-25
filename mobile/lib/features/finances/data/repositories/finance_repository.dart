import 'package:dio/dio.dart';
import '../../../../core/network/api_client.dart';
import '../../../../shared/models/depense.dart';

class FinanceRepository {
  final ApiClient _apiClient;

  FinanceRepository(this._apiClient);

  Future<List<Map<String, dynamic>>> getCategories() async {
    final response = await _apiClient.dio.get('finances/categories/');
    return List<Map<String, dynamic>>.from(response.data);
  }

  Future<List<Depense>> getExpenses({String? periodicite}) async {
    final Map<String, dynamic> queryParams = {};
    if (periodicite != null) {
      queryParams['periodicite'] = periodicite;
    }
    
    final response = await _apiClient.dio.get('finances/', queryParameters: queryParams);
    return (response.data as List).map((e) => Depense.fromJson(e)).toList();
  }

  Future<Depense> createExpense({
    required double montant,
    required String devise,
    required double taux,
    required String description,
    required int? categorieId,
    required String typeDepense,
    required String periodicite,
    String? proofPath,
  }) async {
    FormData formData = FormData.fromMap({
      'montant': montant,
      'devise': devise,
      'taux': taux,
      'description': description,
      'categorie': categorieId,
      'type_depense': typeDepense,
      'periodicite': periodicite,
    });

    if (proofPath != null) {
      formData.files.add(MapEntry(
        'preuve',
        await MultipartFile.fromFile(proofPath),
      ));
    }

    final response = await _apiClient.dio.post('finances/', data: formData);
    return Depense.fromJson(response.data);
  }

  Future<Map<String, dynamic>> getStats() async {
    final response = await _apiClient.dio.get('finances/statistiques/');
    return response.data;
  }
}
