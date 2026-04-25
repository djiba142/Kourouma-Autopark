import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import '../../../../core/theme/app_theme.dart';
import '../bloc/finance_bloc.dart';

class AddExpenseScreen extends StatefulWidget {
  const AddExpenseScreen({super.key});

  @override
  State<AddExpenseScreen> createState() => _AddExpenseScreenState();
}

class _AddExpenseScreenState extends State<AddExpenseScreen> {
  final _formKey = GlobalKey<FormState>();
  final _descController = TextEditingController();
  final _amountController = TextEditingController();
  final _rateController = TextEditingController(text: "8500");
  
  String _selectedType = 'ENTREPRISE';
  String _selectedDevise = 'GNF';
  String _selectedPeriode = 'JOUR';
  int? _selectedCategorie;
  File? _proofImage;

  @override
  Widget build(BuildContext context) {
    return BlocListener<FinanceBloc, FinanceState>(
      listener: (context, state) {
        if (state is FinanceLoaded) {
          // Success after creation
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("Dépense enregistrée avec succès"), backgroundColor: AppTheme.successColor),
          );
          Navigator.pop(context);
        } else if (state is FinanceError) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(state.message), backgroundColor: AppTheme.errorColor),
          );
        }
      },
      child: Scaffold(
        backgroundColor: AppTheme.backgroundColor,
        appBar: AppBar(title: const Text("Nouvelle Dépense")),
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildSectionTitle("Détails de la dépense"),
                const SizedBox(height: 20),
                _buildTextField("Description", "Ex: Carburant livraison Gnégné", _descController, isRequired: true),
                const SizedBox(height: 20),
                _buildAmountRow(),
                const SizedBox(height: 20),
                _buildDropdowns(),
                const SizedBox(height: 30),
                _buildProofPicker(),
                const SizedBox(height: 40),
                ElevatedButton(
                  onPressed: _submitForm,
                  child: const Text("ENREGISTRER LA DÉPENSE"),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(title, style: GoogleFonts.outfit(fontSize: 18, fontWeight: FontWeight.bold));
  }

  Widget _buildTextField(String label, String hint, TextEditingController controller, {bool isRequired = false, TextInputType? keyboardType}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Colors.grey)),
        const SizedBox(height: 8),
        TextFormField(
          controller: controller,
          keyboardType: keyboardType,
          style: const TextStyle(fontSize: 16),
          decoration: InputDecoration(hintText: hint, fillColor: Colors.white),
          validator: (value) => isRequired && (value == null || value.isEmpty) ? "Champ obligatoire" : null,
        ),
      ],
    );
  }

  Widget _buildAmountRow() {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          flex: 2,
          child: _buildTextField("Montant", "0.0", _amountController, isRequired: true, keyboardType: TextInputType.number),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text("Devise", style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Colors.grey)),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                value: _selectedDevise,
                items: const [
                  DropdownMenuItem(value: 'GNF', child: Text('GNF')),
                  DropdownMenuItem(value: 'USD', child: Text('USD')),
                ],
                onChanged: (v) => setState(() => _selectedDevise = v!),
                decoration: const InputDecoration(fillColor: Colors.white),
              ),
            ],
          ),
        ),
        if (_selectedDevise == 'USD') ...[
          const SizedBox(width: 16),
          Expanded(
            child: _buildTextField("Taux", "8500", _rateController, isRequired: true, keyboardType: TextInputType.number),
          ),
        ],
      ],
    );
  }

  Widget _buildDropdowns() {
    final state = context.watch<FinanceBloc>().state;
    List<Map<String, dynamic>> categories = [];
    if (state is FinanceLoaded) {
      categories = state.categories;
    }

    return Column(
      children: [
        _buildDropdownField<int>(
          label: "Catégorie",
          value: _selectedCategorie,
          items: categories.map((c) => DropdownMenuItem(value: c['id'] as int, child: Text(c['nom']))).toList(),
          onChanged: (v) => setState(() => _selectedCategorie = v),
        ),
        const SizedBox(height: 20),
        Row(
          children: [
            Expanded(
              child: _buildDropdownField<String>(
                label: "Type",
                value: _selectedType,
                items: const [
                  DropdownMenuItem(value: 'ENTREPRISE', child: Text('Professionnelle')),
                  DropdownMenuItem(value: 'PERSONNEL', child: Text('Personnelle')),
                ],
                onChanged: (v) => setState(() => _selectedType = v!),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: _buildDropdownField<String>(
                label: "Périodicité",
                value: _selectedPeriode,
                items: const [
                  DropdownMenuItem(value: 'JOUR', child: Text('Journalier')),
                  DropdownMenuItem(value: 'SEMAINE', child: Text('Hebdomadaire')),
                  DropdownMenuItem(value: 'MOIS', child: Text('Mensuel')),
                  DropdownMenuItem(value: 'AN', child: Text('Annuel')),
                ],
                onChanged: (v) => setState(() => _selectedPeriode = v!),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildDropdownField<T>({required String label, required T? value, required List<DropdownMenuItem<T>> items, required ValueChanged<T?> onChanged}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Colors.grey)),
        const SizedBox(height: 8),
        DropdownButtonFormField<T>(
          value: value,
          items: items,
          onChanged: onChanged,
          decoration: const InputDecoration(fillColor: Colors.white),
        ),
      ],
    );
  }

  Widget _buildProofPicker() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text("Justificatif / Reçu", style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Colors.grey)),
        const SizedBox(height: 12),
        GestureDetector(
          onTap: _pickImage,
          child: Container(
            height: 150,
            width: double.infinity,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.grey[200]!),
            ),
            child: _proofImage != null 
              ? ClipRRect(borderRadius: BorderRadius.circular(16), child: Image.file(_proofImage!, fit: BoxFit.cover))
              : const Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.camera_alt_outlined, size: 40, color: AppTheme.primaryColor),
                    SizedBox(height: 8),
                    Text("Prendre une photo du reçu", style: TextStyle(color: Colors.grey)),
                  ],
                ),
          ),
        ),
      ],
    );
  }

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.camera);
    if (picked != null) {
      setState(() => _proofImage = File(picked.path));
    }
  }

  void _submitForm() {
    if (_formKey.currentState!.validate()) {
      context.read<FinanceBloc>().add(CreateExpense(
        montant: double.parse(_amountController.text),
        devise: _selectedDevise,
        taux: double.parse(_rateController.text),
        description: _descController.text,
        categorieId: _selectedCategorie,
        typeDepense: _selectedType,
        periodicite: _selectedPeriode,
        proofPath: _proofImage?.path,
      ));
    }
  }
}
