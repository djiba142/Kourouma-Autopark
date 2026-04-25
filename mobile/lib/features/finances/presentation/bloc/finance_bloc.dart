import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../data/repositories/finance_repository.dart';
import '../../../../shared/models/depense.dart';

// Events
abstract class FinanceEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class LoadFinances extends FinanceEvent {
  final String? periodicite;
  LoadFinances({this.periodicite});
  
  @override
  List<Object?> get props => [periodicite];
}

class CreateExpense extends FinanceEvent {
  final double montant;
  final String devise;
  final double taux;
  final String description;
  final int? categorieId;
  final String typeDepense;
  final String periodicite;
  final String? proofPath;

  CreateExpense({
    required this.montant,
    required this.devise,
    required this.taux,
    required this.description,
    this.categorieId,
    required this.typeDepense,
    required this.periodicite,
    this.proofPath,
  });

  @override
  List<Object?> get props => [montant, devise, taux, description, categorieId, typeDepense, periodicite, proofPath];
}

// States
abstract class FinanceState extends Equatable {
  @override
  List<Object?> get props => [];
}

class FinanceInitial extends FinanceState {}
class FinanceLoading extends FinanceState {}

class FinanceLoaded extends FinanceState {
  final List<Depense> expenses;
  final Map<String, dynamic> stats;
  final List<Map<String, dynamic>> categories;

  FinanceLoaded({
    required this.expenses,
    required this.stats,
    required this.categories,
  });

  @override
  List<Object?> get props => [expenses, stats, categories];
}

class FinanceError extends FinanceState {
  final String message;
  FinanceError(this.message);
  
  @override
  List<Object?> get props => [message];
}

// Bloc
class FinanceBloc extends Bloc<FinanceEvent, FinanceState> {
  final FinanceRepository _repository;

  FinanceBloc(this._repository) : super(FinanceInitial()) {
    on<LoadFinances>(_onLoadFinances);
    on<CreateExpense>(_onCreateExpense);
  }

  Future<void> _onLoadFinances(LoadFinances event, Emitter<FinanceState> emit) async {
    emit(FinanceLoading());
    try {
      final expenses = await _repository.getExpenses(periodicite: event.periodicite);
      final stats = await _repository.getStats();
      final categories = await _repository.getCategories();
      
      emit(FinanceLoaded(
        expenses: expenses,
        stats: stats,
        categories: categories,
      ));
    } catch (e) {
      emit(FinanceError(e.toString()));
    }
  }

  Future<void> _onCreateExpense(CreateExpense event, Emitter<FinanceState> emit) async {
    try {
      await _repository.createExpense(
        montant: event.montant,
        devise: event.devise,
        taux: event.taux,
        description: event.description,
        categorieId: event.categorieId,
        typeDepense: event.typeDepense,
        periodicite: event.periodicite,
        proofPath: event.proofPath,
      );
      add(LoadFinances()); // Refresh
    } catch (e) {
      emit(FinanceError(e.toString()));
    }
  }
}
