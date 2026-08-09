from pathlib import Path


def replace_exact(path: str, old: str, new: str):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"anchor not found in {path}: {old[:80]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")

# UI: checkbox directly beside the install split button.
replace_exact(
    "Raven/Views/AppPage.xaml",
    '''                        </SplitButton>\n                        <Button\n                            x:Name="ShareButton"''',
    '''                        </SplitButton>\n                        <CheckBox\n                            x:Name="DisableRegistrationPathCheckBox"\n                            Margin="4,0,0,0"\n                            VerticalAlignment="Center"\n                            Content="Disable registration and add to PATH"\n                            Visibility="Collapsed" />\n                        <Button\n                            x:Name="ShareButton"'''
)

# Normal labels: checkbox decides whether the package is registered or portable.
replace_exact(
    "Raven/Views/AppPage.xaml.cs",
    '''        // Portable mode: packaged apps are downloaded, unpacked, and launched instead of registered.\n        "Install" => "Download & Run",\n        "Update" => "Update & Run",''',
    '''        "Install" => "Install",\n        "Update" => "Update",'''
)

# Show the option only for MSIX/AppX style package installs, not Win32 installers.
replace_exact(
    "Raven/Views/AppPage.xaml.cs",
    '''        InstallDependenciesSeparatelyToggle.IsChecked = downloadItem?.InstallDependenciesSeparately ?? false;\n\n        if (downloadItem != null)''',
    '''        InstallDependenciesSeparatelyToggle.IsChecked = downloadItem?.InstallDependenciesSeparately ?? false;\n        DisableRegistrationPathCheckBox.Visibility =\n            productInfo.InstallerType == InstallerType.Unpackaged\n                ? Visibility.Collapsed\n                : Visibility.Visible;\n\n        if (downloadItem != null)'''
)

# Capture the user's selection once at the start of the operation.
replace_exact(
    "Raven/Views/AppPage.xaml.cs",
    '''        var isUnpackaged = _currentProductInfo.InstallerType == InstallerType.Unpackaged;\n        var action = CurrentActionKey;\n\n        // For Retry,''',
    '''        var isUnpackaged = _currentProductInfo.InstallerType == InstallerType.Unpackaged;\n        var action = CurrentActionKey;\n        var disableRegistrationAndAddToPath =\n            !isUnpackaged && DisableRegistrationPathCheckBox.IsChecked == true;\n\n        // For Retry,'''
)

old = '''                        try\n                        {\n                            UpdateService.SetDetails("Unpacking package...");\n                            DetailsText.Text = "Unpacking package...";\n\n                            var dependencyPaths = currentItem.DownloadedFiles\n                                .Where(f => !string.Equals(f.Path, mainPackagePath, StringComparison.OrdinalIgnoreCase))\n                                .Select(f => f.Path)\n                                .ToList();\n\n                            var result = await PortableMsixLauncher.ExtractAndLaunchAsync(\n                                mainPackagePath,\n                                dependencyPaths,\n                                _currentProductInfo.Title,\n                                productId,\n                                _downloadCts.Token\n                            );\n\n                            UpdateService.SetDetails($"Portable folder: {result.ExtractDirectory}");\n                            DetailsText.Text = $"Portable folder: {result.ExtractDirectory}";\n                        }\n                        catch (Exception ex)\n                        {\n                            _logger.LogError(\n                                ex,\n                                "Portable extraction/launch failed | ProductId={ProductId} | Package={Package}",\n                                productId,\n                                mainPackagePath\n                            );\n\n                            await ShowErrorDialogAsync(\n                                "Portable launch failed",\n                                ex.Message\n                            );\n                        }'''

new = '''                        var dependencyPaths = currentItem.DownloadedFiles\n                            .Where(f => !string.Equals(f.Path, mainPackagePath, StringComparison.OrdinalIgnoreCase))\n                            .Select(f => f.Path)\n                            .Where(File.Exists)\n                            .ToList();\n\n                        if (disableRegistrationAndAddToPath)\n                        {\n                            try\n                            {\n                                UpdateService.SetDetails("Choose install folder...");\n                                DetailsText.Text = "Choose install folder...";\n\n                                var result = await PortableMsixLauncher.ExtractAndLaunchAsync(\n                                    mainPackagePath,\n                                    dependencyPaths,\n                                    _currentProductInfo.Title,\n                                    productId,\n                                    _downloadCts.Token,\n                                    addToUserPath: true,\n                                    createStartMenuShortcut: true\n                                );\n\n                                UpdateService.SetDetails($"Portable folder: {result.ExtractDirectory}");\n                                DetailsText.Text = $"Portable folder: {result.ExtractDirectory}";\n                            }\n                            catch (Exception ex)\n                            {\n                                _logger.LogError(\n                                    ex,\n                                    "Portable extraction/launch failed | ProductId={ProductId} | Package={Package}",\n                                    productId,\n                                    mainPackagePath\n                                );\n                                await ShowErrorDialogAsync("Portable launch failed", ex.Message);\n                            }\n                        }\n                        else\n                        {\n                            try\n                            {\n                                UpdateService.SetDetails("Installing package...");\n                                DetailsText.Text = "Installing package...";\n                                var progress = new Progress<AppPackageInstaller.InstallProgress>(p =>\n                                    downloadManager.UpdateDownloadProgress(productId, Math.Clamp(p.Percent, 0, 100)));\n\n                                await AppPackageInstaller.InstallAsync(\n                                    mainPackagePath,\n                                    dependencyPackagePaths: dependencyPaths,\n                                    progress: progress,\n                                    installDependenciesSeparately: InstallDependenciesSeparatelyToggle.IsChecked\n                                );\n                            }\n                            catch (Exception ex)\n                            {\n                                _logger.LogError(ex, "Package installation failed | ProductId={ProductId}", productId);\n                                await InstallHelper.ShowInstallationErrorDialogAsync(\n                                    this.Content.XamlRoot,\n                                    "Install_Dialog_Title".GetLocalized(),\n                                    ex\n                                );\n                            }\n                        }'''
replace_exact("Raven/Views/AppPage.xaml.cs", old, new)
