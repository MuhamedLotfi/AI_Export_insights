import 'package:flutter/material.dart';
import 'package:syncfusion_flutter_charts/charts.dart';
import 'package:data_table_2/data_table_2.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_theme.dart';

class SyncfusionChartWidget extends StatelessWidget {
  final Map<String, dynamic> chartData;

  const SyncfusionChartWidget({
    Key? key,
    required this.chartData,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (chartData.isEmpty) return const SizedBox.shrink();

    final type = chartData['type'] as String? ?? 'bar';
    final title = chartData['title'] as String? ?? 'Data Visualization';
    final showDataTable = chartData['show_data_table'] == true;
    final meta = chartData['metadata'] as Map<String, dynamic>? ?? {};
    final dataCount = meta['data_count'] as int? ?? 0;

    return Container(
      margin: const EdgeInsets.only(top: 16, bottom: 8),
      decoration: BoxDecoration(
        color: AppTheme.darkSurface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.2),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header
          _buildHeader(title, type, dataCount),
          
          const Divider(height: 1, color: Colors.white10),

          // Chart Area (skip for table-only responses)
          if (type != 'table')
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: SizedBox(
                height: 300,
                child: _buildChart(type),
              ),
            ),

          // Optional Data Table
          if (showDataTable && chartData['data_rows'] != null) ...[
            const Divider(height: 1, color: Colors.white10),
            _buildDataTable(),
          ],
        ],
      ),
    );
  }

  Widget _buildHeader(String title, String type, int count) {
    IconData icon;
    switch (type) {
      case 'pie':
        icon = Icons.pie_chart;
        break;
      case 'line':
        icon = Icons.show_chart;
        break;
      case 'table':
        icon = Icons.table_chart;
        break;
      case 'bar':
      default:
        icon = Icons.bar_chart;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.02),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: AppTheme.primaryColor.withOpacity(0.2),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, size: 18, color: AppTheme.primaryColor),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              title,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 15,
                fontWeight: FontWeight.w600,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (count > 0)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                '$count items',
                style: const TextStyle(
                  color: Colors.white70,
                  fontSize: 11,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildChart(String type) {
    final labels = List<String>.from(chartData['labels'] ?? []);
    final datasets = chartData['datasets'] as List?;
    if (labels.isEmpty || datasets == null || datasets.isEmpty) {
      return _buildEmptyState();
    }

    final values = List<double>.from(
        (datasets[0]['data'] as List).map((e) => (e as num).toDouble()));

    if (values.isEmpty || values.length != labels.length) {
      return _buildEmptyState();
    }

    final meta = chartData['metadata'] as Map<String, dynamic>? ?? {};
    final xAxisTitle = meta['x_axis_title'] as String? ?? '';
    final yAxisTitle = meta['y_axis_title'] as String? ?? '';
    final valueFormat = meta['value_format'] as String? ?? 'number';
    final showLegend = chartData['show_legend'] == true;

    // Build Chart Data Objects
    final List<_ChartData> data = [];
    for (int i = 0; i < labels.length; i++) {
      data.add(_ChartData(labels[i], values[i]));
    }

    // Number format for axes and tooltips
    final NumberFormat format = _getFormat(valueFormat);

    if (type == 'pie') {
      return SfCircularChart(
        legend: Legend(
          isVisible: showLegend,
          position: LegendPosition.bottom,
          textStyle: const TextStyle(color: Colors.white70),
          overflowMode: LegendItemOverflowMode.wrap,
        ),
        tooltipBehavior: TooltipBehavior(
          enable: true,
          format: 'point.x: point.y',
          textStyle: const TextStyle(color: Colors.white),
          color: AppTheme.darkCard,
        ),
        series: <CircularSeries>[
          DoughnutSeries<_ChartData, String>(
            dataSource: data,
            xValueMapper: (_ChartData data, _) => data.x,
            yValueMapper: (_ChartData data, _) => data.y,
            dataLabelSettings: const DataLabelSettings(
              isVisible: true,
              labelPosition: ChartDataLabelPosition.outside,
              textStyle: TextStyle(color: Colors.white, fontSize: 11),
            ),
            enableTooltip: true,
            explode: true,
            explodeGesture: ActivationMode.singleTap,
            animationDuration: 1000,
          )
        ],
      );
    }

    // Cartesian Charts (Bar / Line)
    return SfCartesianChart(
      plotAreaBorderWidth: 0,
      primaryXAxis: CategoryAxis(
        title: AxisTitle(
          text: xAxisTitle,
          textStyle: const TextStyle(color: Colors.white54, fontSize: 11),
        ),
        majorGridLines: const MajorGridLines(width: 0),
        axisLine: const AxisLine(width: 1, color: Colors.white24),
        labelStyle: const TextStyle(color: Colors.white70, fontSize: 11),
        labelIntersectAction: AxisLabelIntersectAction.rotate45,
      ),
      primaryYAxis: NumericAxis(
        title: AxisTitle(
          text: yAxisTitle,
          textStyle: const TextStyle(color: Colors.white54, fontSize: 11),
        ),
        numberFormat: format,
        axisLine: const AxisLine(width: 0),
        majorTickLines: const MajorTickLines(size: 0),
        majorGridLines: const MajorGridLines(
            width: 1, color: Colors.white10, dashArray: <double>[5, 5]),
        labelStyle: const TextStyle(color: Colors.white54, fontSize: 11),
      ),
      tooltipBehavior: TooltipBehavior(
        enable: true,
        header: '',
        format: 'point.x\npoint.y',
        textStyle: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
        color: AppTheme.primaryColor.withOpacity(0.9),
      ),
      zoomPanBehavior: ZoomPanBehavior(
        enablePinching: true,
        enablePanning: true,
      ),
      series: type == 'line'
          ? <CartesianSeries>[
              SplineAreaSeries<_ChartData, String>(
                dataSource: data,
                xValueMapper: (_ChartData data, _) => data.x,
                yValueMapper: (_ChartData data, _) => data.y,
                gradient: LinearGradient(
                  colors: [
                    AppTheme.primaryColor.withOpacity(0.5),
                    AppTheme.primaryColor.withOpacity(0.0)
                  ],
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                ),
                borderColor: AppTheme.primaryColor,
                borderWidth: 2,
                markerSettings: const MarkerSettings(isVisible: true),
                animationDuration: 1500,
              )
            ]
          : <CartesianSeries>[
              ColumnSeries<_ChartData, String>(
                dataSource: data,
                xValueMapper: (_ChartData data, _) => data.x,
                yValueMapper: (_ChartData data, _) => data.y,
                gradient: LinearGradient(
                  colors: [AppTheme.primaryColor, AppTheme.secondaryColor],
                  begin: Alignment.bottomCenter,
                  end: Alignment.topCenter,
                ),
                borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
                animationDuration: 1000,
              )
            ],
    );
  }

  Widget _buildDataTable() {
    final rawColumns = List<String>.from(chartData['data_columns'] ?? []);
    // Filter out internal metadata columns (e.g. _source, _relevance)
    final columns = rawColumns.where((c) => !c.startsWith('_')).toList();
    final rowsData = chartData['data_rows'] as List?;

    if (columns.isEmpty || rowsData == null || rowsData.isEmpty) {
      return const SizedBox.shrink();
    }

    // Limit to max 50 rows for performance inline
    final displayRows = rowsData.take(50).toList();
    final isTruncated = rowsData.length > 50;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Row(
            children: [
              const Icon(Icons.table_chart_outlined, size: 16, color: Colors.white54),
              const SizedBox(width: 8),
              const Text(
                'Data View',
                style: TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w600),
              ),
              const Spacer(),
              if (isTruncated)
                Text(
                  'Showing first 50 of ${rowsData.length}',
                  style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 11),
                ),
            ],
          ),
        ),
        SizedBox(
          height: 250,
          child: _DataTableView(columns: columns, displayRows: displayRows),
        ),
        const SizedBox(height: 8),
      ],
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.insert_chart_outlined, size: 48, color: Colors.white.withOpacity(0.2)),
          const SizedBox(height: 12),
          Text(
            'Unable to render chart',
            style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 14),
          ),
        ],
      ),
    );
  }

  NumberFormat _getFormat(String formatType) {
    switch (formatType) {
      case 'currency':
        return NumberFormat.simpleCurrency(decimalDigits: 0, name: 'EGP');
      case 'percent':
        return NumberFormat.percentPattern();
      case 'integer':
      case 'number':
      default:
        return NumberFormat.decimalPattern()..maximumFractionDigits = 1;
    }
  }
}

class _ChartData {
  _ChartData(this.x, this.y);
  final String x;
  final double y;
}

class _DataTableView extends StatefulWidget {
  final List<String> columns;
  final List<dynamic> displayRows;

  const _DataTableView({
    Key? key,
    required this.columns,
    required this.displayRows,
  }) : super(key: key);

  @override
  State<_DataTableView> createState() => _DataTableViewState();
}

class _DataTableViewState extends State<_DataTableView> {
  late final ScrollController _horizontalController;
  late final ScrollController _verticalController;

  @override
  void initState() {
    super.initState();
    _horizontalController = ScrollController();
    _verticalController = ScrollController();
  }

  @override
  void dispose() {
    _horizontalController.dispose();
    _verticalController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return DataTable2(
      scrollController: _verticalController,
      horizontalScrollController: _horizontalController,
      columnSpacing: 16,
      horizontalMargin: 16,
      minWidth: widget.columns.length * 120.0,
      headingRowColor: MaterialStateProperty.all(Colors.white.withOpacity(0.03)),
      headingRowHeight: 40,
      dataRowHeight: 48,
      dividerThickness: 1,
      columns: widget.columns.map((col) {
        return DataColumn2(
          label: Text(
            col.replaceAll('_', ' ').toUpperCase(),
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 11,
              fontWeight: FontWeight.bold,
              letterSpacing: 0.5,
            ),
          ),
          size: ColumnSize.L,
        );
      }).toList(),
      rows: widget.displayRows.map((row) {
        final Map<String, dynamic> rowMap = Map<String, dynamic>.from(row as Map);
        return DataRow(
          color: MaterialStateProperty.resolveWith<Color>((Set<MaterialState> states) {
            return widget.displayRows.indexOf(row) % 2 == 0
                ? Colors.transparent
                : Colors.white.withOpacity(0.01);
          }),
          cells: widget.columns.map((col) {
            var value = rowMap[col];
            var textValue = value?.toString() ?? '-';
            
            // Format numbers with thousand separators
            if (value is num) {
              if (value == value.roundToDouble() && value is! double || value == value.toInt()) {
                textValue = NumberFormat('#,###').format(value.toInt());
              } else {
                textValue = NumberFormat('#,###.##').format(value);
              }
            } else if (value is String) {
              // Handle string-encoded numbers from JSON
              final parsed = num.tryParse(value);
              if (parsed != null && value.length > 0 && !value.startsWith('0')) {
                if (parsed == parsed.toInt()) {
                  textValue = NumberFormat('#,###').format(parsed.toInt());
                } else {
                  textValue = NumberFormat('#,###.##').format(parsed);
                }
              }
            }
            
            return DataCell(
              Text(
                textValue,
                style: const TextStyle(color: Colors.white, fontSize: 12),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            );
          }).toList(),
        );
      }).toList(),
    );
  }
}
